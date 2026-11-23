# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PowerbiWorkspace(models.Model):
    _name = "powerbi.workspace"
    _inherit = ['mail.thread']
    _description = "Power BI Workspace/Group"

    name = fields.Char(string="Workspace Name", required=True, tracking=True)
    description = fields.Text(string="Description")
    powerbi_id = fields.Char(
        string="Workspace Power BI Id", size=50, readonly=True)
    state = fields.Selection(
        [('topublish', 'To Publish'), ('published', 'Published')],
        compute="_compute_state",
        string="State",
        tracking=True
    )
    is_published = fields.Boolean(string="Is Published", default=False)
    default_workspace = fields.Boolean(
        string="Default Workspace", default=False)
    responsible_users = fields.Many2many(
        'res.users', string="Responsible Users", tracking=True)
    count_total_eventhouse = fields.Integer(
        compute='_compute_totals', string='Eventhouses')
    count_total_database = fields.Integer(
        compute='_compute_totals', string='Databases')
    count_total_dataset = fields.Integer(
        compute='_compute_totals', string='Datasets')
    count_total_report = fields.Integer(
        compute='_compute_totals', string='Reports')
    count_total_dashboard = fields.Integer(
        compute='_compute_totals', string='Dashboards')
    fabric_group = fields.Boolean(
        string="Fabric Group", compute="_compute_fabric_group")

    def _compute_fabric_group(self):
        config = self.env['ir.config_parameter'].sudo()
        check = config.get_param('res.config.settings.group_powerbi_fabric')
        for rec in self:
            rec.fabric_group = check

    def _compute_totals(self):
        '''This Method Used to Count Related Eventhouses, Databases, Datasets, Reports and Dashboards Of Current Workspace'''
        total_eventhouse = self.env['powerbi.eventhouse'].search_count(
            [('workspace_id', '=', self.id)])
        total_database = self.env['powerbi.kql.database'].search_count(
            [('workspace_id', '=', self.id)])
        total_dataset = self.env['powerbi.dataset'].search_count(
            [('workspace_id', '=', self.id)])
        total_report = self.env['powerbi.report'].search_count(
            [('workspace_id', '=', self.id)])
        total_dashboard = self.env['powerbi.dashboard'].search_count(
            [('workspace_id', '=', self.id)])
        self.count_total_eventhouse = total_eventhouse
        self.count_total_database = total_database
        self.count_total_dataset = total_dataset
        self.count_total_report = total_report
        self.count_total_dashboard = total_dashboard

    def action_redirect(self):
        '''This Method Used To Redirect To Related Dataset And Table of Current Workspace'''
        model_name = self._context.get("model_name")
        name = self._context.get("name")
        domain = [('workspace_id', '=', self.id)]
        return {
            "type": "ir.actions.act_window",
            'name': name,
            'res_model': model_name,
            'domain': domain,
            'view_mode': 'list,form',
            'target': 'current'
        }

    @api.model_create_multi
    def create(self, vals):
        if (len([True for val in vals if val.get('default_workspace')]) > 1):
            raise ValidationError(
                'Warning: Can\'t create more than 1 default workspace.')
        recs = self.search([('default_workspace', '=', True)])
        for val in vals:
            if val.get('default_workspace'):
                if len(recs) > 0:
                    raise ValidationError(
                        'Warning: Can\'t create more than 1 default workspace.')
        return super(PowerbiWorkspace, self).create(vals)

    def write(self, vals):
        if vals.get('default_workspace'):
            if len(self) > 1:
                raise ValidationError(
                    'Warning: Can\'t create more than 1 default workspace.')
            else:
                recs = self.search([('default_workspace', '=', True)])
                recs -= self
                if len(recs) > 0:
                    raise ValidationError(
                        'Warning: Can\'t create more than 1 default workspace.')
        return super(PowerbiWorkspace, self).write(vals)

    @api.depends("is_published")
    def _compute_state(self):
        for rec in self:
            if rec.is_published == True:
                rec.state = "published"
            else:
                rec.state = "topublish"

    def action_publish(self):
        return self.publish_to_powerbi()

    def publish_to_powerbi(self):
        '''This Method Used to Publish Workspaces at Power BI End '''
        success, failure, already_published = [], [], []
        msg = ""
        msgModel = self.env["powerbi.message.wizard"]
        connObj = self.env["powerbi.connection"].get_active_connection()
        if not connObj:
            return msgModel.generated_message("No active connection found!")

        url = f"{connObj.api_url}/{connObj.version == 'powerbi' and 'groups' or 'v1/workspaces'}"
        scopes = ['Workspace.ReadWrite.All']
        connection = connObj._create_powerbi_connection(scopes)
        for workspace in self:
            if workspace.is_published:
                already_published.append(workspace.id)
                continue
            if connObj.version == "powerbi":
                if workspace.default_workspace:
                    continue
                data = {
                    "name": workspace.name,
                }
            else:
                data = {
                    "displayName": workspace.name,
                    "description": workspace.description,
                    "type": "Workspace"
                }
            resp = self.env["powerbi.synchronization"].callPowerbiApi(
                url, 'post', data, connection.get('token', ''), scopes)
            if resp.get('status', False):
                value = resp.get('value')
                pb_workspace_id = value.get('id', False)
                if connObj.access_method == 'sp' and pb_workspace_id:
                    resp_message = self._add_workspace_user(
                        pb_workspace_id, connObj, connection.get('token'))
                    if resp_message:
                        workspace.message_post(body=resp_message)
                workspace.write({
                    "powerbi_id": pb_workspace_id,
                    "is_published": True
                })
                success.append(workspace.name)
            else:
                failure.append(workspace.id)
                msg += f"Workspace export error: Reason - {resp.get('message')}"

        if success:
            msg += f"workspace {str(success)}  successfully published."
        if already_published:
            msg += f"{len(already_published)} workspaces(s) are already published."

        return msgModel.generated_message(msg)

    def _add_workspace_user(self, pb_workspace_id, connObj, token):
        email_list = [email.strip()
                      for email in connObj.sp_users_email.split(',')]
        msg = ""
        for email in email_list:
            data = {
                "emailAddress": email,
                "groupUserAccessRight": "Admin"
            }
            url = f"{connObj._default_powerbi_api_url()}/groups/{pb_workspace_id}/users"
            resp = self.env["powerbi.synchronization"].callPowerbiApi(
                url, 'post', data, token)

            if not resp.get('status', False):
                try:
                    msg += f"Error in User({email}) add: {resp.get('value')['error']['message']}."
                except Exception as KeyError:
                    msg += f"Error in User({email}) add: {resp.get('message')}."
        return msg

    @api.model
    def _create_sale_order_data(self):
        '''This Method Use To Create Demo Data'''
        saleModule = self.env["ir.module.module"].search(
            [('name', '=', 'sale'), ('state', '=', 'installed')], limit=1)
        if saleModule:
            modelObj = self.env["ir.model"].search(
                [("model", "=", "sale.order")], limit=1)
            model = modelObj.model
            workspace = self.search([], limit=1)
            if not workspace:
                workspace = self.create({"name": "My Workspace"})
            eventhouse = self.env["powerbi.eventhouse"].search([], limit=1)
            if not eventhouse:
                eventhouse = eventhouse.create({
                    "name": "Odoo Eventhouse",
                    "workspace_id": workspace.id,
                    "description": "Eventhouse for Odoo data"
                })
            database = self.env["powerbi.kql.database"].create({
                "name": "Odoo Sales",
                "eventhouse_id": eventhouse.id,
                "description": "Database for Odoo sales data"
            })
            table = self.env["powerbi.table"].create({
                "name": "Sales",
                "database_id": database.id,
                "model_id": modelObj.id,
                "model_name": model
            })
            self._create_table_column(model, table, [
                "name"
                "amount_total"
                "date_order"
            ])
        return True

    @api.model
    def _create_invoice_data(self):
        invModule = self.env["ir.module.module"].search(
            [('name', '=', 'account'), ('state', '=', 'installed')], limit=1)
        if invModule:
            modelObj = self.env["ir.model"].search(
                [("model", "=", "account.move")], limit=1)
            model = modelObj.model
            workspace = self.search([], limit=1)
            if not workspace:
                workspace = self.create({"name": "My Workspace"})
            eventhouse = self.env["powerbi.eventhouse"].search([], limit=1)
            if not eventhouse:
                eventhouse = eventhouse.create({
                    "name": "Odoo Eventhouse",
                    "workspace_id": workspace.id,
                    "description": "Eventhouse for Odoo data"
                })
            database = self.env["powerbi.kql.database"].create({
                "name": "Odoo Invoices",
                "eventhouse_id": eventhouse.id,
                "description": "Database for Odoo invoices data"
            })
            table = self.env["powerbi.table"].create({
                "name": "Invoices",
                "database_id": database.id,
                "model_id": modelObj.id,
                "model_name": model
            })
            self._create_table_column(model, table, [
                "name"
                "amount_total"
                "invoice_date"
                "invoice_origin"
                "move_type"
            ])
        return True

    @api.model
    def _create_stock_data(self):
        stockModule = self.env["ir.module.module"].search(
            [('name', '=', 'stock'), ('state', '=', 'installed')], limit=1)
        if stockModule:
            modelObj = self.env["ir.model"].search(
                [("model", "=", "stock.move")], limit=1)
            model = modelObj.model
            workspace = self.search([], limit=1)
            if not workspace:
                workspace = self.create({"name": "My Workspace"})
            eventhouse = self.env["powerbi.eventhouse"].search([], limit=1)
            if not eventhouse:
                eventhouse = eventhouse.create({
                    "name": "Odoo Eventhouse",
                    "workspace_id": workspace.id,
                    "description": "Eventhouse for Odoo data"
                })
            database = self.env["powerbi.kql.database"].create({
                "name": "Odoo Inventory",
                "eventhouse_id": eventhouse.id,
                "description": "Database for Odoo inventory data"
            })
            table = self.env["powerbi.table"].create({
                "name": "Inventory",
                "database_id": database.id,
                "model_id": modelObj.id,
                "model_name": model
            })
            self._create_table_column(model, table, [
                "name"
                "origin"
                "price_unit"
            ])
        return True

    @api.model
    def _create_purchase_data(self):
        purchaseModule = self.env["ir.module.module"].search(
            [('name', '=', 'purchase'), ('state', '=', 'installed')], limit=1)
        if purchaseModule:
            modelObj = self.env["ir.model"].search(
                [("model", "=", "purchase.order")], limit=1)
            model = modelObj.model
            workspace = self.search([], limit=1)
            if not workspace:
                workspace = self.create({"name": "My Workspace"})
            eventhouse = self.env["powerbi.eventhouse"].search([], limit=1)
            if not eventhouse:
                eventhouse = eventhouse.create({
                    "name": "Odoo Eventhouse",
                    "workspace_id": workspace.id,
                    "description": "Eventhouse for Odoo data"
                })
            database = self.env["powerbi.kql.database"].create({
                "name": "Odoo Purchase",
                "eventhouse_id": eventhouse.id,
                "description": "Database for Odoo purchase data"
            })
            table = self.env["powerbi.table"].create({
                "name": "Purchase",
                "database_id": database.id,
                "model_id": modelObj.id,
                "model_name": model
            })
            self._create_table_column(model, table, [
                "name"
                "origin"
                "amount_total"
                "date_order"
            ])
        return True

    @api.model
    def _create_pos_data(self):
        posModule = self.env["ir.module.module"].search(
            [('name', '=', 'point_of_sale'), ('state', '=', 'installed')], limit=1)
        if posModule:
            modelObj = self.env["ir.model"].search(
                [("model", "=", "pos.order")], limit=1)
            model = modelObj.model
            workspace = self.search([], limit=1)
            if not workspace:
                workspace = self.create({"name": "My Workspace"})
            eventhouse = self.env["powerbi.eventhouse"].search([], limit=1)
            if not eventhouse:
                eventhouse = eventhouse.create({
                    "name": "Odoo Eventhouse",
                    "workspace_id": workspace.id,
                    "description": "Eventhouse for Odoo data"
                })
            database = self.env["powerbi.kql.database"].create({
                "name": "Odoo POS",
                "eventhouse_id": eventhouse.id,
                "description": "Database for Odoo POS data"
            })
            table = self.env["powerbi.table"].create({
                "name": "POS",
                "database_id": database.id,
                "model_id": modelObj.id,
                "model_name": model
            })
            self._create_table_column(model, table, [
                "name"
                "amount_total"
                "date_order"
            ])
        return True

    def _create_table_column(self, model, table, fields):
        '''This Method Used to Create Table Column For Demo Data'''
        for field in fields:
            field_id = self.env["ir.model.fields"].search(
                [('model_id.model', '=', model), ('name', '=', field)], limit=1)
            if field_id:
                self.env["powerbi.table.column"].create({
                    "table_id": table.id,
                    "field_id": field_id.id,
                    "label": field_id.field_description.replace(' ', '_')
                })
