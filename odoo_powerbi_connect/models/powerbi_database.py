# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import logging
import time
from markupsafe import Markup
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PowerbiKQLDatabase(models.Model):
    _name = "powerbi.kql.database"
    _inherit = ['mail.thread']
    _description = "Power BI KQL Database"

    name = fields.Char(string="Database Name", required=True, tracking=True)
    description = fields.Text(string="Description")
    powerbi_id = fields.Char(
        string="Database Power BI Id", size=50, readonly=True)
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
        related="eventhouse_id.workspace_id"
    )
    eventhouse_id = fields.Many2one(
        "powerbi.eventhouse",
        string="Eventhouse",
        required=True,
        default=lambda self: self._compute_default_eventhouse()
    )
    table_ids = fields.One2many(
        "powerbi.table",
        inverse_name="database_id",
        string="Tables",
        readonly=True
    )
    count_total_table = fields.Integer(
        compute='_compute_tables', string='#Tables')
    query_service_uri = fields.Char(string="Query Service URI")
    ingestion_service_uri = fields.Char(string="Ingestion Service URI")

    def _compute_tables(self):
        '''This method is used to count related tables of current database'''
        total_table = self.env['powerbi.table'].search_count(
            [('database_id', '=', self.id)])
        self.count_total_table = total_table

    def _compute_default_eventhouse(self):
        if self._context.get('active_model') == 'powerbi.eventhouse':
            return self._context.get('active_id')

    @api.depends("is_published")
    def _compute_state(self):
        for rec in self:
            if rec.is_published == True:
                rec.state = "published"
            else:
                rec.state = "topublish"

    def action_redirect(self):
        '''This method is used to redirect to related tables of current database'''
        ctx = dict(self._context or {})
        model_name = ctx.get("model_name")
        name = ctx.get("name")
        domain = [('database_id', '=', self.id)]
        ctx['fabric_group'] = self.workspace_id.fabric_group
        ctx['default_database_id'] = self.id
        return {
            "type": "ir.actions.act_window",
            'name': name,
            'res_model': model_name,
            'domain': domain,
            'view_mode': 'list,form',
            'target': 'current',
            'context': ctx
        }

    def action_publish(self):
        return self.publish_to_powerbi()

    def action_unpublish(self):
        ctx = dict(self._context or {})
        ctx.update({
            'default_operation_object': 'kql.database',
            'default_operation': 'delete',
        })
        return {
            'name': 'Unpublish KQL Database',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'unpublish.message.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': ctx
        }

    def publish_to_powerbi(self):
        '''This method is used to publish KQL Database at Power BI end'''
        success, failure, already_published, eventhouse_not_published = [], [], [], []
        msg = ""
        msgModel = self.env["powerbi.message.wizard"]
        connObj = self.env["powerbi.connection"].get_active_connection()
        if not connObj:
            return msgModel.generated_message("No active connection found!")
        scopes = ["KQLDatabase.ReadWrite.All",
                  "Item.ReadWrite.All", "Workspace.Read.All"]
        connection = connObj._create_powerbi_connection(scopes)
        for database in self:
            if database.is_published:
                already_published.append(database.id)
                continue
            if not database.eventhouse_id.is_published:
                eventhouse_not_published.append(database.id)
                continue
            url = f"{connObj.api_url}/v1/workspaces/{database.workspace_id.powerbi_id}/kqlDatabases"
            data = {
                "displayName": database.name,
                "description": database.description,
                "creationPayload": {
                    "databaseType": "ReadWrite",
                    "parentEventhouseItemId": database.eventhouse_id.powerbi_id
                }
            }
            resp = self.env["powerbi.synchronization"].callPowerbiApi(
                url, 'post', data, connection.get('token', ''), scopes)
            if resp.get('status', False):
                value = resp.get('value')
                database.write({
                    "powerbi_id": value and value.get('id', False),
                    "is_published": True
                })
                success.append(database.id)
                message = f'KQL Database {database.name} successfully published to Power BI.'
                database.message_post(body=message)
            else:
                failure.append(database.id)
                message = f"KQL Database could not be published.<br/>Reason:- {str(resp.get('message'))}"
                database.message_post(body=Markup(message))

        if success:
            # fetching powerbi id, ingestion and query service uri after 10 secs for successful databases.
            time.sleep(10)
            self.browse(success).fetch_kql_db_details(connObj, connection)

            msg += f"{len(success)} database(s) successfully published."
        if failure:
            msg += f"{len(failure)} database(s) failed to publish."
        if already_published:
            msg += f"{len(already_published)} database(s) already published."
        if eventhouse_not_published:
            msg += f"{len(eventhouse_not_published)} database(s) eventhouse not yet published, first publish eventhouse."
        return msgModel.generated_message(msg)

    def fetch_kql_db_details(self, connObj, connection):
        for database in self:
            url = f"{connObj.api_url}/v1/workspaces/{database.workspace_id.powerbi_id}/kqlDatabases"
            resp = self.env["powerbi.synchronization"].callPowerbiApi(
                url, 'get', token=connection.get('token', ''))
            if resp.get('status', False):
                value = resp.get('value')
                for db in value.get('value', []):
                    if db.get('properties', {}).get('parentEventhouseItemId') == database.eventhouse_id.powerbi_id:
                        if db.get('displayName') == database.name:
                            database.write({
                                "powerbi_id": db.get('id', False),
                                "is_published": True,
                                "query_service_uri": db.get('properties', {}).get('queryServiceUri'),
                                "ingestion_service_uri": db.get('properties', {}).get('ingestionServiceUri')
                            })
                    elif db.get('workspaceId') == database.workspace_id.powerbi_id:
                        if db.get('displayName') == database.name:
                            database.write({
                                "powerbi_id": db.get('id', False),
                                "is_published": True,
                                "query_service_uri": db.get('properties', {}).get('queryServiceUri'),
                                "ingestion_service_uri": db.get('properties', {}).get('ingestionServiceUri')
                            })
        return True

    def action_fetch_kql_db_details(self):
        connObj = self.env["powerbi.connection"].get_active_connection()
        if not connObj:
            return False
        scopes = ["KQLDatabase.ReadWrite.All", "Item.ReadWrite.All"]
        connection = connObj._create_powerbi_connection(scopes)
        return self.fetch_kql_db_details(connObj, connection)

    def unpublish_powerbi(self, operation, reason):
        ''' This method is used to unpublish KQL Database from Power BI or Odoo based on the operation type.'''
        msg = ""
        msgModel = self.env["powerbi.message.wizard"]
        success, failure, not_published = [], [], []
        scopes = ["KQLDatabase.ReadWrite.All", "Item.ReadWrite.All"]
        connObj = self.env["powerbi.connection"].get_active_connection()
        if not connObj:
            return msgModel.generated_message("No active connection found!")
        connection = connObj._create_powerbi_connection(scopes)
        for database in self:
            if not database.is_published:
                not_published.append(database.name)
                continue
            if operation == 'delete':
                url = f"{connObj.api_url}/v1/workspaces/{database.workspace_id.powerbi_id}/kqlDatabases/{database.powerbi_id}"
                resp = self.env["powerbi.synchronization"].callPowerbiApi(
                    url, 'delete', token=connection.get('token', ''), scope=scopes)
                if resp.get('status', False):
                    database.write({
                        "powerbi_id": False,
                        "is_published": False,
                        "query_service_uri": False,
                        "ingestion_service_uri": False
                    })
                    database.table_ids.write({
                        "is_published": False,
                        "last_sync_datetime": False
                    })
                    success.append(database.name)
                    message = f'KQL Database {database.name} successfully unpublished from Power BI.<br/>Reason:- {reason}'
                    database.message_post(body=Markup(message))
                else:
                    failure.append(database.name)
                    message = f"KQL Database could not be unpublished.<br/>Reason:- {str(resp.get('message'))}"
                    database.message_post(body=Markup(message))
            else:
                return msgModel.generated_message(
                    "Operation type 'unlink' is not implemented for KQL Database.")

        if success:
            msg += f"{len(success)} database(s) successfully unpublished."
        if failure:
            msg += f"{len(failure)} database(s) failed to unpublish."
        if not_published:
            msg += f"<br/>Databases ({', '.join(not_published)}) have not been published yet!"

        return msgModel.generated_message(msg)
