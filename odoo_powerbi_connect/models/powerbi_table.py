# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.data_format import DataFormat
from azure.kusto.data.exceptions import KustoApiError
from azure.kusto.ingest import (
    IngestionProperties,
    ManagedStreamingIngestClient,
    ReportLevel,
    IngestionStatus
)

import re
import pytz
import pandas
import ast
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from markupsafe import Markup
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

MAX_BATCH_SIZE = 10000  # Maximum number of table records to export in a single batch


class PowerbiTable(models.Model):
    _name = "powerbi.table"
    _inherit = ['mail.thread']
    _description = "Powerbi Table"

    _powerbiKQLDatatypes = {
        "char": "string",
        "text": "string",
        "html": 'string',
        "selection": "string",
        "float": "real",
        "integer": "int",
        "monetary": "real",
        "boolean": "bool",
        "many2one": "string",
        "date": "datetime",
        "datetime": "datetime",
        "many2many": "string",
        "one2many": "string",
        "json": "string"
    }

    name = fields.Char(string="Table Name", required=True, tracking=True)
    dataset_id = fields.Many2one(
        "powerbi.dataset",
        string="Dataset",
        domain="[('is_published','!=',True)]",
        default=lambda self: self._compute_default_dataset())
    database_id = fields.Many2one(
        "powerbi.kql.database",
        string="KQL Database",
        default=lambda self: self._compute_default_database())
    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        ondelete="set null",
        tracking=True,
        domain=[('transient', '!=', True)]
    )
    model_name = fields.Char(string="Model Name")
    column_ids = fields.One2many(
        "powerbi.table.column",
        inverse_name="table_id",
        string="Table Fields",
    )
    filter_domain = fields.Char(string="Domain")
    state = fields.Selection(
        [('topublish', 'To Publish'), ('published', 'Published')],
        compute="_compute_state",
        string="State",
        tracking=True
    )
    is_published = fields.Boolean(string="Is Published", default=False)
    is_modified = fields.Boolean(string="Modified", default=False)
    run_cron = fields.Boolean(string="Export Data Using Cron",
                              help='Check this to enable automatic data export from odoo to powerbi via cron.', default=False)
    export_action = fields.Integer(string="Action Id", default=0)
    last_sync_datetime = fields.Datetime("Last Sync Datetime",
                                         help="This Datetime will be used during export operation.\nThe records created after this date will be exported to powerbi.\nThis will be updated after every export operation.")
    use_relation = fields.Boolean("Use Table Relationship", default=False,
                                  help="Check this field if you want to manage relationship for this table based on primary key and foreign key (by Many2one field).")
    select_all_columns = fields.Boolean(string="Select All Columns",
                                        help="Check this field to auto select all the columns from selected model in this table.")
    data_export_mode = fields.Selection(
        [('all', 'Whole Data'), ('new', 'Incremental Data')],
        string="Data Export Mode",
        default='new',
        tracking=True,
        required=True,
        help="Select 'Whole' to export all the records from model to powerbi.\nSelect 'Incremental' to export only the new records created after 'Last Sync Datetime'."
    )
    fabric_group = fields.Boolean(
        string="Fabric Group", compute="_compute_fabric_group")
    dataset_type = fields.Selection(related="dataset_id.dataset_type")
    page_size = fields.Integer('Page Size', default=10000)

    def _compute_fabric_group(self):
        config = self.env['ir.config_parameter'].sudo()
        check = config.get_param('res.config.settings.group_powerbi_fabric')
        for rec in self:
            rec.fabric_group = check

    _sql_constraints = [
        (
            'dataset_table_unique',
            'unique (dataset_id,name)',
            'Table name must be unique per dataset.',
        ),
        (
            'klq_database_table_unique',
            'unique (database_id,name)',
            'Table name must be unique per kql database.',
        )
    ]

    @api.constrains('page_size')
    def _check_page_size(self):
        for record in self:
            if record.page_size < 1:
                raise ValidationError("Page Size should be positive.")

    def _compute_default_database(self):
        if self._context.get('active_model') == 'powerbi.kql.database':
            return self._context.get('active_id')

    def _compute_default_dataset(self):
        ctx = self._context
        if ctx.get('active_model') == 'powerbi.dataset' and not self.env['powerbi.dataset'].browse(ctx.get('active_id')).is_published:
            return ctx.get('active_id')

    @api.depends("is_published")
    def _compute_state(self):
        for rec in self:
            if rec.is_published == True:
                rec.state = "published"
            else:
                rec.state = "topublish"

    @api.onchange("model_id", "select_all_columns")
    def onchange_model(self):
        self.model_name = self.model_id.model
        self.column_ids = [(6, 0, [])]
        if self.select_all_columns:
            self._create_column(self.model_id.field_id.filtered(
                lambda f: f.ttype != 'one2many' and f.name != 'id'))
        else:
            common_fields = ["name", "amount_total", "date_order", "invoice_origin",
                             "invoice_date", "move_type", "origin", "price_unit", "state",]
            fields_to_create = self.model_id.field_id.filtered(
                lambda f: f.name in common_fields)
            self._create_column(fields_to_create)

    def _create_column(self, fields_to_create):
        vals_list = []
        for field in fields_to_create:
            vals_list.append((0, 0, {
                "field_id": field.id,
                "field_type": field.ttype,
                "label": field.field_description.replace(' ', '_')
            }))
        if vals_list:
            self.column_ids = vals_list

    @api.constrains("name")
    def validate_table_name(self):
        for table in self:
            if table.name:
                if not bool(re.fullmatch(r'[A-Za-z0-9_]*', table.name)):
                    raise UserError(
                        _("Table name can only contain alphabets, digits or underscore."))

    def write(self, vals):
        if "column_ids" in vals:
            vals.update(is_modified=True)
        return super(PowerbiTable, self).write(vals)

    def action_publish_table(self):
        success, failure, already_published, database_not_published = [], [], [], []
        msg = ""
        msgModel = self.env["powerbi.message.wizard"]
        connObj = self.env["powerbi.connection"].get_active_connection()
        if not connObj:
            return msgModel.generated_message("No active connection found!")
        for table in self:
            if table.is_published:
                already_published.append(table.id)
                continue
            if not table.database_id.is_published:
                database_not_published.append(table.id)
                continue

            try:
                if connObj.access_method == "mu":
                    kcsb = KustoConnectionStringBuilder.with_aad_user_password_authentication(
                        table.database_id.query_service_uri, connObj.user, connObj.pwd, connObj.tenent_id)
                else:
                    kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
                        table.database_id.query_service_uri, connObj.client_id, connObj.client_secret, connObj.tenent_id)

                with KustoClient(kcsb) as client:
                    query = table.get_table_definition(True)
                    response = client.execute(table.database_id.name, query)
                    if not response.get_exceptions():
                        success.append(table.id)
                        table.write({
                            "is_published": True,
                            "is_modified": False
                        })
                        message = "Table successfully published on Power BI"
                        table.message_post(body=message)
            except KustoApiError as e:
                message = f"Table could not be published.<br/>Reason:- {str(e.error.description)}"
                table.message_post(body=Markup(message))
                failure.append(table.id)
            except Exception as e:
                message = f"Table could not be published.<br/>Reason:- {str(e)}"
                table.message_post(body=Markup(message))
                failure.append(table.id)

        if success:
            msg += f"{len(success)} tables(s) successfully published."
        if failure:
            msg += f"{len(failure)} tables(s) failed to publish."
        if already_published:
            msg += f"{len(already_published)} tables(s) already published."
        if database_not_published:
            msg += f"{len(database_not_published)} table(s) KQL database not yet published, first publish KQL database."

        return msgModel.generated_message(msg)

    def action_toggle_cron(self):
        self.run_cron = not self.run_cron

    def action_unpublish_table(self):
        ctx = dict(self._context or {})
        ctx['default_operation_object'] = 'table'
        return {
            'name': 'Unpublish Table',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'unpublish.message.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': ctx
        }

    def action_export(self):
        return self.export_to_powerbi()

    def action_delete(self):
        return self.delete_powerbi_data()

    def action_update_schema(self):
        return self.update_table_schema()

    def export_to_powerbi(self):
        success, failure, not_published, no_data = [], [], 0, 0
        msg = ""
        msgModel = self.env["powerbi.message.wizard"]
        connObj = self.env["powerbi.connection"].get_active_connection()
        if not connObj:
            return msgModel.generated_message("No active connection found!")
        if connObj.version == "fabric":
            return self.export_to_fabric()
        scopes = ["Dataset.ReadWrite.All"]
        connection = connObj._create_powerbi_connection(scopes)
        for table in self:
            if not table.is_published:
                not_published += 1
                continue
            model = self.env[table.model_id.model]
            domain = []
            if table.filter_domain:
                domain = ast.literal_eval(table.filter_domain)

            # for date field
            if hasattr(model, 'create_date'):
                date_field = 'create_date'
            elif hasattr(model, 'date'):
                date_field = 'date'
            elif hasattr(model, 'date_order'):
                date_field = 'date_order'
            elif hasattr(model, 'invoice_date'):
                date_field = 'invoice_date'
            else:
                date_field = False

            total_limit = connObj.record_sync_limit if table.data_export_mode == 'new' else None
            if date_field and table.data_export_mode == 'new' and table.last_sync_datetime:
                domain = expression.AND(
                    [[(date_field, '>', table.last_sync_datetime)], domain])
            elif table.data_export_mode == 'all' and table.last_sync_datetime:
                table.delete_powerbi_data()

            records = model.search(
                domain, order=f'{date_field} asc', limit=total_limit)
            rows = []
            for rec in records:
                rows.append(table.get_row_data(rec))
            if not rows:
                no_data += 1
                continue
            if table.dataset_id.workspace_id.default_workspace:
                url = f"{connObj.api_url}/datasets/{table.dataset_id.powerbi_id}/tables/{table.name}/rows"
            else:
                url = f"{connObj.api_url}/groups/{table.dataset_id.workspace_id.powerbi_id}/datasets/{table.dataset_id.powerbi_id}/tables/{table.name}/rows"

            total_rows = len(rows)
            start = 0
            while start < total_rows:
                end = min(start + MAX_BATCH_SIZE, total_rows)
                temp_rows = rows[start:end]

                data = {"rows": temp_rows}
                resp = self.env["powerbi.synchronization"].callPowerbiApi(
                    url, "post", data=data, token=connection.get('token'), scope=scopes
                )

                if resp.get('status'):
                    if table.id not in success:
                        success.append(table.id)
                    table.last_sync_datetime = getattr(
                        records[end - 1], date_field)
                else:
                    if table.id not in failure:
                        failure.append(table.id)
                    message = f"Table data could not be exported.<br/>Reason:- {str(resp.get('message'))}"
                    table.message_post(body=Markup(message))
                    break

                start = end

        if success:
            tables = self.browse(success)
            for table in tables:
                table.message_post(
                    body="Table Data successfully exported to Power Bi.")
            msg += f"{len(success)} table data successfully exported."
        if failure:
            msg += f"{len(failure)} table data can't be exported."
        if not_published:
            msg += f"{not_published} tables not published yet."
        if no_data:
            msg += f"{no_data} tables have no data to export."

        return msgModel.generated_message(msg)

    def export_to_fabric(self):
        success, failure, not_published, no_data = [], [], 0, 0
        msg = ""
        msgModel = self.env["powerbi.message.wizard"]
        connObj = self.env["powerbi.connection"].get_active_connection()
        if not connObj:
            return msgModel.generated_message("No active connection found!")
        for table in self:
            if not table.is_published:
                not_published += 1
                continue
            model = self.env[table.model_id.model]
            domain = []
            if table.filter_domain:
                domain = ast.literal_eval(table.filter_domain)

            # for date field
            if hasattr(model, 'create_date'):
                date_field = 'create_date'
            elif hasattr(model, 'date'):
                date_field = 'date'
            elif hasattr(model, 'date_order'):
                date_field = 'date_order'
            elif hasattr(model, 'invoice_date'):
                date_field = 'invoice_date'
            else:
                date_field = False

            total_limit = connObj.record_sync_limit
            if date_field and table.data_export_mode == 'new' and table.last_sync_datetime:
                domain = expression.AND(
                    [[(date_field, '>', table.last_sync_datetime)], domain])
            elif table.data_export_mode == 'all' and table.last_sync_datetime:
                table.delete_fabric_data()
                total_limit = None

            records = model.search(
                domain, order=f'{date_field} asc', limit=total_limit)

            data_fields = table.get_table_fields()
            data_rows = []
            for rec in records:
                data_rows.append(table.get_row_data_fabric(rec))
            if not data_rows:
                no_data += 1
                continue

            status = table._data_ingest(data_fields, data_rows, connObj)
            if status:
                if table.id not in success:
                    success.append(table.id)
                table.last_sync_datetime = getattr(records[-1], date_field)
            else:
                if table.id not in failure:
                    failure.append(table.id)

        if success:
            msg += f"{len(success)} table data successfully exported."
        if failure:
            msg += f"{len(failure)} table data can't be exported."
        if not_published:
            msg += f"{not_published} tables not published yet."
        if no_data:
            msg += f"{no_data} tables have no data to export."

        return msgModel.generated_message(msg)

    def _data_ingest(self, data_fields, data_rows, connObj):
        self.ensure_one()
        status = False
        try:
            if connObj.access_method == "mu":
                kcsb = KustoConnectionStringBuilder.with_aad_user_password_authentication(
                    self.database_id.ingestion_service_uri, connObj.user, connObj.pwd, connObj.tenent_id)
            else:
                kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
                    self.database_id.ingestion_service_uri, connObj.client_id, connObj.client_secret, connObj.tenent_id)

            with ManagedStreamingIngestClient(kcsb) as client:
                ingestion_props = IngestionProperties(
                    database=self.database_id.name,
                    table=self.name,
                    data_format=DataFormat.CSV,
                    report_level=ReportLevel.FailuresAndSuccesses
                )

                df = pandas.DataFrame(data=data_rows, columns=data_fields)

                result = client.ingest_from_dataframe(
                    df, ingestion_properties=ingestion_props)
                if result and result.status == IngestionStatus.SUCCESS:
                    message = "Table Data successfully exported to Power Bi."
                    self.message_post(body=message)
                    status = True
        except KustoApiError as e:
            message = f"Table data could not be exported.<br/>Error:- {str(e.error.description)}"
            self.message_post(body=Markup(message))
        except Exception as e:
            message = f"Table data could not be exported.<br/>Reason:- {str(e)}"
            self.message_post(body=Markup(message))
        return status

    def get_table_fields(self):
        return ["ID"] + [col.label for col in self.column_ids]

    def get_row_data(self, dataObj):
        self.ensure_one()
        row = {'Id': dataObj.id}
        for column in self.column_ids:
            value = getattr(dataObj, column.name)
            if column.field_type == 'many2one':
                if self.use_relation:
                    row[column.label] = value and value.id or ""
                else:
                    row[column.label] = self._get_rec_name_value(value) or ""
            elif column.field_type == 'many2many':
                if value:
                    m2m_data = ', '.join(
                        [self._get_rec_name_value(val) or "" for val in value])
                    row[column.label] = m2m_data
            elif column.field_type == 'datetime':
                row[column.label] = self.wk_format_date(
                    value) if value else ''
            else:
                row[column.label] = value or '' if column.field_type in [
                    'date'] else value
        return row

    def get_row_data_fabric(self, dataObj):
        self.ensure_one()
        row = [dataObj.id]
        for column in self.column_ids:
            value = getattr(dataObj, column.name)
            if column.field_type == 'many2one':
                row.append(self._get_rec_name_value(value) or "")
            elif column.field_type == 'many2many':
                m2m_data = ""
                if value:
                    m2m_data = ', '.join(
                        [self._get_rec_name_value(val) or "" for val in value])
                row.append(m2m_data)
            elif column.field_type == 'datetime':
                row.append(self.wk_format_date(value) if value else '')
            else:
                row.append(value or '' if column.field_type in [
                           'date'] else value)
        return row

    def _get_rec_name_value(self, obj):
        if obj._rec_name:
            return getattr(obj, obj._rec_name)
        elif hasattr(obj, "name"):
            return obj.name
        elif hasattr(obj, "display_name"):
            return obj.display_name
        else:
            return False

    @api.model
    def wk_format_date(self, date):
        connObj = self.env['powerbi.connection'].get_active_connection()
        utc_date = pytz.utc.localize(date, is_dst=False)
        target_tz = pytz.timezone(connObj.wk_time_zone)
        target_date = utc_date.astimezone(target_tz)
        return target_date.strftime('%Y-%m-%d %H:%M:%S.%f')

    def delete_powerbi_data(self):
        success, failure, not_published = [], [], 0
        msg = ""
        msgModel = self.env["powerbi.message.wizard"]
        connObj = self.env["powerbi.connection"].get_active_connection()
        if not connObj:
            return msgModel.generated_message("No active connection found!")
        if connObj.version == "fabric":
            return self.delete_fabric_data()
        scopes = ["Dataset.ReadWrite.All"]
        connection = connObj._create_powerbi_connection(scopes)
        for table in self:
            if not table.is_published:
                not_published += 1
                continue
            if table.dataset_id.workspace_id.default_workspace:
                url = f"{connObj.api_url}/datasets/{table.dataset_id.powerbi_id}/tables/{table.name}/rows"
            else:
                url = f"{connObj.api_url}/groups/{table.dataset_id.workspace_id.powerbi_id}/datasets/{table.dataset_id.powerbi_id}/tables/{table.name}/rows"
            resp = self.env["powerbi.synchronization"].callPowerbiApi(
                url, "delete", token=connection.get('token', ''), scope=scopes)
            if resp.get('status'):
                success.append(table.id)
                table.last_sync_datetime = False
                message = "Table data successfully deleted on Power BI"
                table.message_post(body=message)
            else:
                failure.append(table.id)
                message = f"Table data could not be deleted.<br/>Reason:- {str(resp.get('message'))}"
                table.message_post(body=Markup(message))

        if success:
            msg += f"{len(success)} table data successfully deleted."
        if failure:
            msg += f"{len(failure)} table data can't be deleted."
        if not_published:
            msg += f"{not_published} tables not published yet."

        return msgModel.generated_message(msg)

    def delete_fabric_data(self):
        success, failure, not_published = [], [], 0
        msg = ""
        msgModel = self.env["powerbi.message.wizard"]
        connObj = self.env["powerbi.connection"].get_active_connection()
        if not connObj:
            return msgModel.generated_message("No active connection found!")
        for table in self:
            if not table.is_published:
                not_published += 1
                continue

            try:
                if connObj.access_method == "mu":
                    kcsb = KustoConnectionStringBuilder.with_aad_user_password_authentication(
                        table.database_id.query_service_uri, connObj.user, connObj.pwd, connObj.tenent_id)
                else:
                    kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
                        table.database_id.query_service_uri, connObj.client_id, connObj.client_secret, connObj.tenent_id)

                with KustoClient(kcsb) as client:
                    query = f".clear table {table.name} data"
                    response = client.execute(table.database_id.name, query)
                    if not response.get_exceptions():
                        success.append(table.id)
                        table.last_sync_datetime = False
                        message = "Table data successfully deleted on Power BI"
                        table.message_post(body=message)
            except KustoApiError as e:
                message = f"Table data could not be deleted.<br/>Reason:- {str(e.error.description)}"
                table.message_post(body=Markup(message))
                failure.append(table.id)
            except Exception as e:
                message = f"Table data could not be deleted.<br/>Reason:- {str(e)}"
                table.message_post(body=Markup(message))
                failure.append(table.id)

        if success:
            msg += f"{len(success)} table data successfully deleted."
        if failure:
            msg += f"{len(failure)} table data can't be deleted."
        if not_published:
            msg += f"{not_published} tables not published yet."

        return msgModel.generated_message(msg)

    def update_table_schema(self):
        success, failure, not_published, no_columns, invalid = [], [], 0, 0, 0
        msg = ""
        msgModel = self.env["powerbi.message.wizard"]
        connObj = self.env["powerbi.connection"].get_active_connection()
        if not connObj:
            return msgModel.generated_message("No active connection found!")
        if connObj.version == "fabric":
            return self.update_table_schema_fabric()
        scopes = ["Dataset.ReadWrite.All"]
        connection = connObj._create_powerbi_connection(scopes)
        for table in self:
            if not table.is_published:
                not_published += 1
                continue
            if table.use_relation and not table.validate_table_relation():
                invalid += 1
                continue
            columns = self.env["powerbi.dataset"].get_table_columns(table)
            if not columns:
                no_columns += 1
                continue
            data = {
                "name": table.name,
                "columns": columns
            }
            if table.dataset_id.workspace_id.default_workspace:
                url = f"{connObj.api_url}/datasets/{table.dataset_id.powerbi_id}/tables/{table.name}"
            else:
                url = f"{connObj.api_url}/groups/{table.dataset_id.workspace_id.powerbi_id}/datasets/{table.dataset_id.powerbi_id}/tables/{table.name}"
            resp = self.env["powerbi.synchronization"].callPowerbiApi(
                url, "put", data=data, token=connection.get('token'), scope=scopes)
            if resp.get('status'):
                table.is_modified = False
                success.append(table.id)
                message = "Table schema successfully updated on Power BI"
                table.message_post(body=message)
            else:
                failure.append(table.id)
                message = f"Table schema could not be updated.<br/>Reason:- {str(resp.get('message'))}"
                table.message_post(body=Markup(message))

        if success:
            msg += f"{len(success)} tables successfully updated.\n"
        if failure:
            msg += f"{len(failure)} tables can't be updated.\n"
        if not_published:
            msg += f"{not_published} tables not published yet.\n"
        if no_columns:
            msg += f"{no_columns} tables does not have any columns to update.\n"
        if invalid:
            msg += f"{invalid} tables are not valid.\n"

        return msgModel.generated_message(msg)

    def update_table_schema_fabric(self):
        success, failure, not_published = [], [], 0
        msg = ""
        msgModel = self.env["powerbi.message.wizard"]
        connObj = self.env["powerbi.connection"].get_active_connection()
        if not connObj:
            return msgModel.generated_message("No active connection found!")
        for table in self:
            if not table.is_published:
                not_published += 1
                continue

            try:
                if connObj.access_method == "mu":
                    kcsb = KustoConnectionStringBuilder.with_aad_user_password_authentication(
                        table.database_id.query_service_uri, connObj.user, connObj.pwd, connObj.tenent_id)
                else:
                    kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
                        table.database_id.query_service_uri, connObj.client_id, connObj.client_secret, connObj.tenent_id)

                with KustoClient(kcsb) as client:
                    query = table.get_table_definition()
                    response = client.execute(table.database_id.name, query)
                    if not response.get_exceptions():
                        success.append(table.id)
                        table.is_modified = False
                        message = "Table schema successfully updated on Power BI"
                        table.message_post(body=message)
            except KustoApiError as e:
                message = f"Table schema could not be updated.<br/>Reason:- {str(e.error.description)}"
                table.message_post(body=Markup(message))
                failure.append(table.id)
            except Exception as e:
                message = f"Table schema could not be updated.<br/>Reason:- {str(e)}"
                table.message_post(body=Markup(message))
                failure.append(table.id)

        if success:
            msg += f"{len(success)} tables successfully updated.\n"
        if failure:
            msg += f"{len(failure)} tables can't be updated.\n"
        if not_published:
            msg += f"{not_published} tables not published yet.\n"

        return msgModel.generated_message(msg)

    def get_table_definition(self, create=False):
        self.ensure_one()
        query = f"{create and '.create' or '.alter'} table {self.name} "
        col_query = "ID:int"
        for column in self.column_ids:
            col_query += f", {column.label}:{self._powerbiKQLDatatypes.get(column.field_id.ttype, 'string')}"
        query += f"({col_query})"
        return query

    def create_server_action(self):
        '''This Method Used to Add Server Action For Specific Table'''
        self.ensure_one()
        model_id = self.model_id.id
        name = self.model_id.name
        existing_action = self.search([('model_id', '=', model_id),
                                       ('export_action', '!=', 0)], limit=1)
        if not existing_action:
            message = 'Message: Server Action Created Succesfully For Model %s' % name
            code = "action = env['powerbi.wizard'].start_data_synchronisation()"
            action_server = False
            try:
                action_server = self.env['ir.actions.server'].create({
                    'name': 'Export To Powerbi',
                    'model_id': model_id,
                    'state': 'code',
                    'binding_model_id': model_id,
                    'code': code
                })
            except Exception as e:
                message = 'Message: Error While Creating Server Action: %s' % str(
                    e)
            if action_server:
                self.export_action = action_server.id
        else:
            message = 'Message: Server Action Is Already Created For The Model %s' % name
        return self.env['powerbi.message.wizard'].generated_message(message)

    def delete_server_action(self):
        '''This Method Used to Delete Server Action For Specific Table'''
        self.ensure_one()
        model_id = self.model_id.id
        name = self.model_id.name
        existing_action = self.search([('model_id', '=', model_id),
                                       ('export_action', '!=', 0)], limit=1)

        if existing_action:
            message = 'Server Action deleted successfully for model %s' % name
            action_server = self.env['ir.actions.server'].search(
                [('id', '=', existing_action.export_action)])
            if action_server:
                try:
                    res = action_server.unlink()
                    if res:
                        existing_action.export_action = 0
                except Exception as e:
                    message = 'Error while deleting server action: %s' % str(e)
            else:
                message = "No server action found for the model %s" % name
        else:
            message = "No server action found for the model %s" % name
        return self.env["powerbi.message.wizard"].generated_message(message)

    @api.model
    def powerbi_export_cron(self):
        '''This method is used to export data via cron.'''
        tables = self.search([("is_published", "=", True),
                             ("run_cron", "=", True), ("is_modified", "=", False)])
        if tables:
            tables.export_to_powerbi()
        return True

    def validate_table_relation(self):
        self.ensure_one()
        for column in self.column_ids.filtered(lambda c: c.field_type == 'many2one'):
            related_table = self.dataset_id.table_ids.filtered(
                lambda d: d.model_id.model == column.field_id.relation)
            if not related_table:
                self.message_post(
                    body=f"No table found for model {column.field_id.relation} in dataset {self.dataset_id.name}")
                return False
        return True

    def unpublish_powerbi(self, operation, reason):
        ''' This method is used to unpublish or delete the table from Power BI based on the operation type.'''
        msg = ""
        msgModel = self.env["powerbi.message.wizard"]
        success, failure, not_published = [], [], []
        connObj = self.env["powerbi.connection"].get_active_connection()
        if not connObj:
            return msgModel.generated_message("No active connection found!")
        if connObj.version == "powerbi":
            return msgModel.generated_message("Only Fabric group tables can be unpublished.")
        for table in self:
            if not table.is_published:
                not_published.append(table.name)
                continue
            if operation == 'delete':
                try:
                    if connObj.access_method == "mu":
                        kcsb = KustoConnectionStringBuilder.with_aad_user_password_authentication(
                            table.database_id.query_service_uri, connObj.user, connObj.pwd, connObj.tenent_id)
                    else:
                        kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
                            table.database_id.query_service_uri, connObj.client_id, connObj.client_secret, connObj.tenent_id)

                    with KustoClient(kcsb) as client:
                        query = f".drop table {table.name} ifexists"
                        response = client.execute(
                            table.database_id.name, query)
                        if not response.get_exceptions():
                            table.write({
                                'is_published': False,
                                'last_sync_datetime': False
                            })
                            success.append(table.name)
                            message = f'Table {table.name} successfully deleted from Power BI.<br/>Reason:- {reason}'
                            table.message_post(body=Markup(message))
                        else:
                            failure.append(table.name)
                            message = f"Table could not be deleted.<br/>Reason:- {str(response.get_exceptions())}"
                            table.message_post(body=Markup(message))

                except KustoApiError as e:
                    message = f"Table could not be unpublished.<br/>Reason:- {str(e.error.description)}"
                    table.message_post(body=Markup(message))
                    failure.append(table.id)
                except Exception as e:
                    message = f"Table could not be unpublished.<br/>Reason:- {str(e)}"
                    table.message_post(body=Markup(message))
                    failure.append(table.id)
            else:
                table.write({
                    'is_published': False,
                    'last_sync_datetime': False
                })
                success.append(table.name)
                message = f'Table {table.name} successfully unpublished from odoo.<br/>Reason:- {reason}'
                table.message_post(body=Markup(message))

        if success:
            msg += f"{len(success)} table(s) successfully unpublished."
        if failure:
            msg += f"{len(failure)} table(s) can't be unpublished."
        if not_published:
            msg += f"<br/>Tables({', '.join(not_published)}) have not been published yet!"

        return msgModel.generated_message(msg)
