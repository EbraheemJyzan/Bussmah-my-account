from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BussmaMarketingMaterial(models.Model):
    _inherit = 'bussma.marketing.material'

    financial_request_ids = fields.One2many(
        'financial.request',
        'marketing_material_id',
        string='Financial Requests'
    )
    financial_request_count = fields.Integer(
        string='Financial Request Count',
        compute='_compute_invoice_counts'
    )
    cost_invoice_count = fields.Integer(
        string='Cost Invoices',
        compute='_compute_invoice_counts'
    )
    supplier_invoice_count = fields.Integer(
        string='Supplier Invoices',
        compute='_compute_invoice_counts'
    )
    can_see_financial_buttons = fields.Boolean(
        string='Can See Financial Buttons',
        compute='_compute_can_see_financial_buttons'
    )

    @api.depends_context('uid')
    @api.depends('user_id', 'marketing_id.user_id', 'marketing_id.material_responsible_id', 'department_ids.manager_id', 'stage_id.department_id.manager_id')
    def _compute_can_see_financial_buttons(self):
        user = self.env.user
        is_supervisor = user.has_group('marketing_opportunity_management.group_marketing_supervisor')
        for rec in self:
            is_material_resp = (rec.user_id and rec.user_id == user)
            is_mkt_proj_mgr = rec.marketing_id and (
                (rec.marketing_id.user_id and rec.marketing_id.user_id == user) or
                (rec.marketing_id.material_responsible_id and rec.marketing_id.material_responsible_id == user)
            )
            is_dept_mgr = (
                (rec.department_ids and any(d.manager_id and d.manager_id == user for d in rec.department_ids)) or
                (rec.stage_id and rec.stage_id.department_id and rec.stage_id.department_id.manager_id and rec.stage_id.department_id.manager_id == user)
            )
            rec.can_see_financial_buttons = bool(is_supervisor or is_material_resp or is_mkt_proj_mgr or is_dept_mgr)

    @api.depends('financial_request_ids', 'financial_request_ids.invoice_type', 'financial_request_ids.request_type')
    def _compute_invoice_counts(self):
        for rec in self:
            rec.financial_request_count = len(rec.financial_request_ids)
            cost_reqs = rec.financial_request_ids.filtered(
                lambda r: r.invoice_type == 'cost' or (not r.invoice_type and r.request_type in ['digital_apps_accounts', 'advertising_campaign_costs', 'influencer_campaigns', 'tv_advertisement', 'radio'])
            )
            supplier_reqs = rec.financial_request_ids.filtered(
                lambda r: r.invoice_type == 'supplier' or (not r.invoice_type and r.request_type not in ['digital_apps_accounts', 'advertising_campaign_costs', 'influencer_campaigns', 'tv_advertisement', 'radio'])
            )
            rec.cost_invoice_count = len(cost_reqs)
            rec.supplier_invoice_count = len(supplier_reqs)

    def action_create_financial_request(self):
        self.ensure_one()
        if not self.can_see_financial_buttons:
            raise UserError(_("Sorry, this action is restricted to Marketing Supervisor, Marketing Material Responsible, Department Managers, and Marketing Project Manager only."))

        invoice_type = 'cost'
        request_type = 'digital_apps_accounts'
        if self.material_stage_selection == 'mat_ops_exec':
            invoice_type = 'supplier'
            request_type = 'brochure_printing'

        project_name = False
        if self.marketing_id and self.marketing_id.name:
            project_name = self.marketing_id.name
        elif self.name:
            project_name = self.name

        ctx = {
            'default_requester_id': self.env.user.id,
            'default_department': 'marketing',
            'default_project_name': project_name,
            'default_invoice_type': invoice_type,
            'default_request_type': request_type,
            'default_invoice_description': _("Financial Request for Marketing Material: %s") % (self.name or ''),
            'default_marketing_material_id': self.id,
            'default_marketing_id': self.marketing_id.id if self.marketing_id else False,
        }

        return {
            'name': _('Financial Management Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'financial.request',
            'view_mode': 'form',
            'target': 'new',
            'context': ctx,
        }

    def action_view_cost_invoices(self):
        self.ensure_one()
        if not self.can_see_financial_buttons:
            raise UserError(_("Sorry, this action is restricted to Marketing Supervisor, Marketing Material Responsible, Department Managers, and Marketing Project Manager only."))

        cost_requests = self.financial_request_ids.filtered(
            lambda r: r.invoice_type == 'cost' or (not r.invoice_type and r.request_type in ['digital_apps_accounts', 'advertising_campaign_costs', 'influencer_campaigns', 'tv_advertisement', 'radio'])
        )
        action = {
            'name': _('Cost Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'financial.request',
            'domain': [('id', 'in', cost_requests.ids)],
            'context': {
                'default_marketing_material_id': self.id,
                'default_marketing_id': self.marketing_id.id if self.marketing_id else False,
                'default_department': 'marketing',
                'default_invoice_type': 'cost',
            },
        }
        if len(cost_requests) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = cost_requests.id
        else:
            action['view_mode'] = 'list,form'
        return action

    def action_view_supplier_invoices(self):
        self.ensure_one()
        if not self.can_see_financial_buttons:
            raise UserError(_("Sorry, this action is restricted to Marketing Supervisor, Marketing Material Responsible, Department Managers, and Marketing Project Manager only."))

        supplier_requests = self.financial_request_ids.filtered(
            lambda r: r.invoice_type == 'supplier' or (not r.invoice_type and r.request_type not in ['digital_apps_accounts', 'advertising_campaign_costs', 'influencer_campaigns', 'tv_advertisement', 'radio'])
        )
        action = {
            'name': _('Supplier Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'financial.request',
            'domain': [('id', 'in', supplier_requests.ids)],
            'context': {
                'default_marketing_material_id': self.id,
                'default_marketing_id': self.marketing_id.id if self.marketing_id else False,
                'default_department': 'marketing',
                'default_invoice_type': 'supplier',
            },
        }
        if len(supplier_requests) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = supplier_requests.id
        else:
            action['view_mode'] = 'list,form'
        return action
