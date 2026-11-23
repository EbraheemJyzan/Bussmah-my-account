# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from markupsafe import Markup
from odoo import api, fields, models


class PowerbiEventhouse(models.Model):
    _name = "powerbi.eventhouse"
    _inherit = ['mail.thread']
    _description = "Power BI Eventhouse"

    name = fields.Char(string="Eventhouse Name", required=True, tracking=True)
    description = fields.Text(string="Description")
    powerbi_id = fields.Char(
        string="Eventhouse Power BI Id", size=50, readonly=True)
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
    database_ids = fields.One2many(
        'powerbi.kql.database',
        inverse_name="eventhouse_id",
        string="KQL Databases",
        readonly=True
    )
    count_total_database = fields.Integer(
        compute='_compute_total_database', string='#KQL Databases')

    def _compute_total_database(self):
        '''This method is used to count related KQL Databases of current Eventhouse'''
        count = self.env['powerbi.kql.database'].search_count(
            [('eventhouse_id', '=', self.id)])
        self.count_total_database = count

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

    def action_redirect(self):
        '''This method is used to redirect to related KQL Databases of current Eventhouse'''
        model_name = self._context.get("model_name")
        name = self._context.get("name")
        domain = [('eventhouse_id', '=', self.id)]
        return {
            "type": "ir.actions.act_window",
            'name': name,
            'res_model': model_name,
            'domain': domain,
            'view_mode': 'list,form',
            'target': 'current'
        }

    def action_publish(self):
        return self.publish_to_powerbi()

    def action_unpublish(self):
        ctx = dict(self._context or {})
        ctx['default_operation_object'] = 'eventhouse'
        return {
            'name': 'Unpublish Eventhouse',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'unpublish.message.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': ctx
        }

    def publish_to_powerbi(self):
        '''This method used to publish Eventhouse at Powerbi end'''
        success, failure, already_published, workspace_not_published = [], [], [], []
        msg = ""
        msgModel = self.env["powerbi.message.wizard"]
        connObj = self.env["powerbi.connection"].get_active_connection()
        if not connObj:
            return msgModel.generated_message("No active connection found!")
        scopes = ["Eventhouse.ReadWrite.All", "Item.ReadWrite.All"]
        connection = connObj._create_powerbi_connection(scopes)
        for eventhouse in self:
            if eventhouse.is_published:
                already_published.append(eventhouse.id)
                continue
            if not eventhouse.workspace_id.is_published:
                workspace_not_published.append(eventhouse.id)
                continue

            url = f"{connObj.api_url}/v1/workspaces/{eventhouse.workspace_id.powerbi_id}/eventhouses"
            data = {
                "displayName": eventhouse.name,
                "description": eventhouse.description
            }
            resp = self.env["powerbi.synchronization"].callPowerbiApi(
                url, 'post', data, connection.get('token', ''), scopes)
            if resp.get('status', False):
                value = resp.get('value')
                eventhouse.write({
                    "powerbi_id": value.get('id', False),
                    "is_published": True
                })
                success.append(eventhouse.name)
                message = f'Eventhouse {eventhouse.name} successfully published to Power BI.'
                eventhouse.message_post(body=message)
            else:
                failure.append(eventhouse.name)
                message = f"Eventhouse could not be published.<br/>Reason:- {str(resp.get('message'))}"
                eventhouse.message_post(body=Markup(message))

        if success:
            msg += f"{len(success)} eventhouse(s) successfully published."
        if failure:
            msg += f"{len(failure)} eventhouse(s) failed to publish."
        if already_published:
            msg += f"{len(already_published)} eventhouse(s) already published."
        if workspace_not_published:
            msg += f"{len(workspace_not_published)} eventhouse(s) workspace not yet published, first publish workspace."
        return msgModel.generated_message(msg)

    def unpublish_powerbi(self, operation, reason):
        '''This method is used to unpublish eventhouse at Odoo end and delete at Power BI end'''
        msg = ""
        message = ''
        msgModel = self.env["powerbi.message.wizard"]
        success, failure = [], []
        scopes = ["Eventhouse.ReadWrite.All", "Item.ReadWrite.All"]
        connObj = self.env["powerbi.connection"].get_active_connection()
        connection = connObj._create_powerbi_connection(scopes)
        for eventhouse in self:
            if operation == 'delete':
                url = f"{connObj.api_url}/v1/workspaces/{eventhouse.workspace_id.powerbi_id}/eventhouses/{eventhouse.powerbi_id}"
                resp = self.env["powerbi.synchronization"].callPowerbiApi(
                    url, 'delete', token=connection.get('token', ''), scope=scopes)
                if resp.get('status', False):
                    eventhouse.write({
                        "powerbi_id": False,
                        "is_published": False
                    })
                    eventhouse.database_ids.is_published = False
                    eventhouse.database_ids.table_ids.is_published = False
                    success.append(eventhouse.name)
                    message = f'Eventhouse {eventhouse.name} successfully deleted from Power BI.<br/>Reason:- {reason}'
                    eventhouse.message_post(body=Markup(message))
                else:
                    failure.append(eventhouse.name)
                    message = f"Eventhouse could not be deleted.<br/>Reason:- {str(resp.get('message'))}"
                    eventhouse.message_post(body=Markup(message))
            else:
                eventhouse.write({
                    "powerbi_id": False,
                    "is_published": False
                })
                eventhouse.database_ids.is_published = False
                eventhouse.database_ids.table_ids.is_published = False
                message = f'Eventhouse {eventhouse.name} successfully unpublished from odoo.<br/>Reason:- {reason}'
                eventhouse.message_post(body=Markup(message))

        if success:
            msg += f"{len(success)} eventhouse(s) successfully unpublished."
        if failure:
            msg += f"{len(failure)} eventhouse(s) can't be unpublished."

        return msgModel.generated_message(msg)
