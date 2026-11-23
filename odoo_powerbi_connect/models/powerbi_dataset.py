# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import uuid
from markupsafe import Markup
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PowerbiDataset(models.Model):
    _name = "powerbi.dataset"
    _inherit = ['mail.thread']
    _description = "Power BI Dataset"

    _powerbiDatatypes = {
        "char": "string",
        "text": "string",
        "html": 'string',
        "selection": "string",
        "float": "Double",
        "integer": "Int64",
        "monetary": "Double",
        "boolean": "bool",
        "many2one": "string",
        "date": "DateTime",
        "datetime": "DateTime",
        "many2many": "string",
        "one2many": "string",
        "json": "string"
    }

    name = fields.Char(string="Dataset Name", required=True, tracking=True)
    powerbi_id = fields.Char(
        string="Dataset Power BI Id", size=50, readonly=True)
    dataset_type = fields.Selection(
        [('push', 'Push'), ('import', 'Import')],
        string="Dataset Type",
        required=True,
        default="push",
        tracking=True
    )
    state = fields.Selection(
        [('topublish', 'To Publish'), ('published', 'Published')],
        compute="_compute_state",
        string="State",
        tracking=True
    )
    is_published = fields.Boolean(string="Is Published", default=False)
    workspace_id = fields.Many2one(
        "powerbi.workspace",
        string="Workspace",
        required=True,
        default=lambda self: self._compute_default_workspace()
    )
    table_ids = fields.One2many(
        "powerbi.table",
        inverse_name="dataset_id",
        string="Tables",
        readonly=True
    )
    count_total_table = fields.Integer(
        compute='_compute_tables', string='#Tables')

    web_auth = fields.Selection(
        [("api_key", "API Key"), ("web_token", "Web Token")],
        string="Web Auth Type")
    web_url = fields.Char("Web URL", compute="_compute_web_url")
    web_token = fields.Char("Web Token", readonly=True)
    show_steps = fields.Boolean("Show Steps")

    def _compute_tables(self):
        '''This Method Used to Count Related Tables Of Current Dataset'''
        total_table = self.env['powerbi.table'].search_count(
            [('dataset_id', '=', self.id)])
        self.count_total_table = total_table

    def _compute_default_workspace(self):
        if self._context.get('active_model') == 'powerbi.workspace':
            return self._context.get('active_id')

    @api.depends("is_published")
    def _compute_state(self):
        for rec in self:
            if rec.is_published == True:
                rec.state = "published"
            else:
                rec.state = "topublish"

    @api.depends("web_token")
    def _compute_web_url(self):
        for rec in self:
            web_url = ""
            if rec.dataset_type == "import":
                base_url = self.env["ir.config_parameter"].sudo(
                ).get_param("web.base.url")
                web_url = f"{base_url}/powerbi_dataset/{rec.id}"
                if rec.web_auth == "web_token":
                    web_url += f"/web/{rec.web_token}"
            rec.web_url = web_url

    def reset_web_token(self):
        self.web_token = False
        return True

    def write(self, vals):
        res = super(PowerbiDataset, self).write(vals)
        if res and vals.get("web_auth"):
            self.reset_web_token()
        return res

    def action_redirect(self):
        '''This Method Used To Redirect To Related Tables of Current Dataset'''
        model_name = self._context.get("model_name")
        name = self._context.get("name")
        domain = [('dataset_id', '=', self.id)]
        return {
            "type": "ir.actions.act_window",
            'name': name,
            'res_model': model_name,
            'domain': domain,
            'view_mode': 'list,form',
            'target': 'current'
        }

    def action_set_unpublish(self):
        self.is_published = False
        self.table_ids.is_published = False
        return True

    def action_unpublish(self):
        ctx = dict(self._context or {})
        ctx['default_operation_object'] = 'dataset'
        return {
            'name': 'Message/Summary',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'unpublish.message.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': ctx
        }

    def action_generate_web_token(self):
        self.ensure_one()
        self.web_token = uuid.uuid4().hex
        return True

    def unpublish_powerbi(self, dataset_operation, reason):
        '''This Method Used To Unpublish Dataset At Odoo end And Delete At Powerbi End'''
        msg = ""
        message = ''
        msgModel = self.env["powerbi.message.wizard"]
        success, failure = [], []
        scopes = ['Dataset.ReadWrite.All']
        connObj = self.env["powerbi.connection"].get_active_connection()
        connection = connObj._create_powerbi_connection(scopes)
        for dataset in self:
            if dataset_operation == 'delete':
                if dataset.workspace_id.default_workspace:
                    url = f"{connObj.api_url}/datasets/{dataset.powerbi_id}"
                else:
                    url = f"{connObj.api_url}/groups/{dataset.workspace_id.powerbi_id}/datasets/{dataset.powerbi_id}"
                resp = self.env["powerbi.synchronization"].callPowerbiApi(
                    url, 'delete', token=connection.get('token', ''), scope=scopes)
                if resp.get('status', False):
                    dataset.write({
                        "powerbi_id": False,
                        "is_published": False
                    })
                    dataset.table_ids.is_published = False
                    success.append(dataset.name)
                    message = f'Dataset {dataset.name} successfully deleted from Power BI.<br/>Reason:- {reason}'
                    dataset.message_post(body=Markup(message))
                else:
                    failure.append(dataset.name)
                    message = f"Dataset could not be deleted.<br/>Reason:- {str(resp.get('message'))}"
                    dataset.message_post(body=Markup(message))
            else:
                dataset.write({
                    "powerbi_id": False,
                    "is_published": False
                })
                dataset.table_ids.is_published = False
                success.append(dataset.name)
                message = f'Dataset {dataset.name} successfully unpublished on odoo.<br/>Reason:- {reason}'
                dataset.message_post(body=Markup(message))

        if success:
            msg += f"{len(success)} dataset(s) successfully unpublished."
        if failure:
            msg += f"{len(failure)} dataset(s) can't be unpublished."

        return msgModel.generated_message(msg)

    def action_set_publish(self):
        self.is_published = True
        self.table_ids.is_published = True
        return True

    def action_publish(self):
        return self.publish_to_powerbi()

    def toggle_show_steps(self):
        for rec in self:
            rec.show_steps = not rec.show_steps
        return True

    def publish_to_powerbi(self):
        '''This Method Used To Publish Dataset At Powerbi End'''
        success, failure, already_published, no_tables, invalid = [], [], [], [], []
        workspace_not_published = []
        msg = ""
        msgModel = self.env["powerbi.message.wizard"]

        typeImportDatasets = self.filtered(
            lambda d: d.dataset_type == 'import')
        typePushDatasets = self.filtered(lambda d: d.dataset_type == 'push')
        if typeImportDatasets:
            typeImportDatasets.is_published = True
            msg += f"{len(typeImportDatasets)} datasets set to published."

        if typePushDatasets:
            connObj = self.env["powerbi.connection"].get_active_connection()
            if not connObj:
                return msgModel.generated_message("No active connection found!")
            scopes = ['Dataset.ReadWrite.All']
            connection = connObj._create_powerbi_connection(scopes)
            for dataset in typePushDatasets:
                if dataset.table_ids.filtered(lambda t: t.use_relation and not t.validate_table_relation()):
                    invalid.append(dataset.id)
                    continue
                if dataset.is_published:
                    already_published.append(dataset.id)
                    continue
                if not dataset.workspace_id.is_published:
                    workspace_not_published.append(dataset.id)
                    continue
                if dataset.workspace_id.default_workspace:
                    url = f"{connObj.api_url}/datasets"
                else:
                    url = f"{connObj.api_url}/groups/{dataset.workspace_id.powerbi_id}/datasets"
                tables = dataset.get_tables_data()
                if not tables:
                    no_tables.append(dataset.id)
                    continue
                data = {
                    "name": dataset.name,
                    "defaultMode": "Push",
                    "tables": tables,
                    "relationships": dataset.get_tables_relation()
                }
                resp = self.env["powerbi.synchronization"].callPowerbiApi(
                    url, 'post', data, connection.get('token', ''), scopes)
                if resp.get('status', False):
                    value = resp.get('value')
                    dataset.write({
                        "powerbi_id": value.get("id", False),
                        "is_published": True
                    })
                    dataset.table_ids.write(
                        {"is_published": True, "is_modified": False})
                    success.append(dataset.name)
                    message = f'Dataset {dataset.name} successfully published to Power BI.'
                    dataset.message_post(body=message)
                else:
                    failure.append(dataset.name)
                    message = f"Dataset could not be published.<br/>Reason:- {str(resp.get('message'))}"
                    dataset.message_post(body=Markup(message))

        if success:
            msg += f"{len(success)} dataset(s) successfully published."
        if failure:
            msg += f"{len(failure)} dataset(s) failed to publish."
        if already_published:
            msg += f"{len(already_published)} dataset(s) already published."
        if no_tables:
            msg += f"{len(no_tables)} dataset(s) doesn't contain any table."
        if invalid:
            msg += f"{len(invalid)} dataset(s) tables are not valid."
        if workspace_not_published:
            msg += f"{len(workspace_not_published)} dataset(s) workspace not yet published, first publish workspace."
        return msgModel.generated_message(msg)

    def get_tables_data(self):
        return_data = []
        for table in self.table_ids:
            table_data = {
                "name": table.name,
                "columns": self.get_table_columns(table)
            }
            return_data.append(table_data)
        return return_data

    def get_table_columns(self, table):
        '''This Method Used To Get Table Column Data'''
        columns = [{"name": "Id", "dataType": "string"}]
        for col in table.column_ids:
            columns.append({
                "name": col.label,
                "dataType": self._powerbiDatatypes.get(col.field_type, 'string')
            })
        if len(columns) > 75:
            raise ValidationError(
                "You cannot add more than 75 columns in a table.")
        return columns

    def get_tables_relation(self):
        self.ensure_one
        relations = []
        for table in self.table_ids.filtered(lambda t: t.use_relation):
            for column in table.column_ids.filtered(lambda c: c.field_type == 'many2one'):
                related_table = self.table_ids.filtered(
                    lambda t: t.model_id.model == column.field_id.relation)
                if related_table-table:
                    relations.append({
                        'fromColumn': column.label,
                        'fromTable': table.name,
                        'name': f"{table.name} to {related_table.name} relation",
                        'toColumn': 'Id',
                        'toTable': related_table.name
                    })
        return relations
