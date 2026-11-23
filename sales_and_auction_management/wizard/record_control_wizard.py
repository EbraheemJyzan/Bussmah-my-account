from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RecordControlWizard(models.TransientModel):
    _name = 'record.control.wizard'
    _description = 'Record Control Wizard'

    control_type = fields.Selection([
        ('phase1', 'Phase 1 (Entries)'),
        ('phase2', 'Phase 2 (Management)'),
        ('menu', 'Menu Control'),
        ('project', 'Project'),
    ], string='Control Type', default='phase1', required=True)
    entry_id = fields.Many2one('entries', string='Entry (Phase 1)')
    entry_p2_id = fields.Many2one('sales.auction.management', string='Entry (Phase 2)')
    # Menu Control fields
    menu_id = fields.Many2one('ir.ui.menu', string='Menu Item')
    new_menu_name = fields.Char(string='New Menu Name')
    # Phase 1 fields
    project_path = fields.Selection([
        ('cities', 'Cities'),
        ('specialized', 'Specialized'),
        ('standard', 'Standard')
    ], string='Project Path')
    requires_technical_offer = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Requires Technical Offer')
    is_entry_archive = fields.Boolean(string='Archived Entry')
    is_deferred_opportunities_archive = fields.Boolean(string='Deferred Opportunities Archive')
    is_listing_archive_2023 = fields.Boolean(string='Archived Listings 2023')
    is_technical_offers_archive = fields.Boolean(string='Archived Technical Offers')
    is_partners_screen = fields.Boolean(string='Partners Screen')
    # Phase 2 fields
    request_type_id = fields.Many2one('request.type', string='Phase 2 Path', domain="[('res_model', '=', target_model)]")
    is_move_to_direct_sales = fields.Boolean(string='Move to Direct Sales')
    is_sale_cancelled = fields.Boolean(string='Sale Cancelled')
    is_sold = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Is Sold')
    auction_date = fields.Date(string='Auction Date')
    is_single_project = fields.Boolean(string='Is Single Project')
    # Delete option
    is_delete = fields.Boolean(string='Delete Record', default=False)
    # Project field
    project_id = fields.Many2one('bussma.project', string='Project')

    # Common field
    target_model = fields.Char(compute='_compute_target_model')
    stage_id_domain = fields.Char(compute='_compute_stage_id_domain')
    stage_id = fields.Many2one('request.stage', string='New Stage')
    is_auction_pvt = fields.Boolean(compute='_compute_type_flags')
    is_sales_type = fields.Boolean(compute='_compute_type_flags')
    is_enf_type = fields.Boolean(compute='_compute_type_flags')
    menu_ids_domain = fields.Many2many('ir.ui.menu', compute='_compute_menu_ids_domain')

    @api.depends('control_type')
    def _compute_menu_ids_domain(self):
        menu_data = self.env['ir.model.data'].search([
            ('model', '=', 'ir.ui.menu'),
            ('module', 'in', ['bussma_system', 'sales_and_auction_management'])
        ])
        self.menu_ids_domain = menu_data.mapped('res_id')

    @api.depends('control_type')
    def _compute_target_model(self):
        for rec in self:
            if rec.control_type == 'phase1':
                rec.target_model = 'entries'
            elif rec.control_type == 'phase2':
                rec.target_model = 'sales.auction.management'
            else:
                rec.target_model = False

    @api.depends('control_type', 'request_type_id')
    def _compute_stage_id_domain(self):
        for rec in self:
            domain = [('id', '=', -1)]
            if rec.control_type == 'phase1':
                entry_screen = self.env.ref('bussma_system.entry_screen', raise_if_not_found=False)
                define_path = self.env.ref('bussma_system.define_project_path_assign_analyst', raise_if_not_found=False)
                base_stage_ids = []
                if entry_screen:
                    base_stage_ids.append(entry_screen.id)
                if define_path:
                    base_stage_ids.append(define_path.id)
                if rec.request_type_id:
                    preliminary_type = self.env.ref('bussma_system.preliminary_study', raise_if_not_found=False)
                    detailed_type = self.env.ref('bussma_system.detailed_study', raise_if_not_found=False)
                    city_type = self.env.ref('bussma_system.city_study', raise_if_not_found=False)
                    target_type_id = rec.request_type_id.id
                    if rec.request_type_id == detailed_type and preliminary_type:
                        target_type_id = preliminary_type.id
                    domain = ['&', ('res_model', '=', 'entries'), '|', ('id', 'in', base_stage_ids), ('request_type_ids', 'in', target_type_id)]
                else:
                    domain = [('res_model', '=', 'entries'), ('id', 'in', base_stage_ids)]
            elif rec.control_type == 'phase2':
                if rec.request_type_id:
                    domain = [('request_type_ids', 'in', rec.request_type_id.id)]
                else:
                    domain = [('res_model', '=', 'sales.auction.management')]
            rec.stage_id_domain = str(domain)

    @api.depends('request_type_id')
    def _compute_type_flags(self):
        auction_pvt = self.env.ref('sales_and_auction_management.p2_type_auction_pvt', raise_if_not_found=False)
        sales_type = self.env.ref('sales_and_auction_management.p2_type_sales', raise_if_not_found=False)
        auction_enf = self.env.ref('sales_and_auction_management.p2_type_auction_enf', raise_if_not_found=False)
        for rec in self:
            rec.is_auction_pvt = (rec.request_type_id == auction_pvt)
            rec.is_sales_type = (rec.request_type_id == sales_type)
            rec.is_enf_type = (rec.request_type_id == auction_enf)

    @api.onchange('control_type')
    def _onchange_control_type(self):
        self.entry_id = False
        self.entry_p2_id = False
        self.project_path = False
        self.requires_technical_offer = False
        self.request_type_id = False
        self.stage_id = False
        self.is_entry_archive = False
        self.is_deferred_opportunities_archive = False
        self.is_listing_archive_2023 = False
        self.is_technical_offers_archive = False
        self.is_partners_screen = False
        self.is_move_to_direct_sales = False
        self.is_sale_cancelled = False
        self.is_sold = False
        self.auction_date = False
        self.is_single_project = False
        self.menu_id = False
        self.new_menu_name = False
        self.project_id = False
        if self.control_type in [
            'project',
            'opportunity',
            'marketing',
            'marketing_material',
            'marketing_task',
            'financial_request',
            'hr_request',
        ]:
            self.is_delete = True
        else:
            self.is_delete = False

    @api.onchange('menu_id')
    def _onchange_menu_id(self):
        if self.menu_id:
            self.new_menu_name = self.menu_id.name

    @api.onchange('entry_id')
    def _onchange_entry_id(self):
        if self.entry_id:
            self.project_path = self.entry_id.project_path
            self.requires_technical_offer = self.entry_id.requires_technical_offer
            self.request_type_id = self.entry_id.request_type_id
            self.stage_id = self.entry_id.stage_id
            self.is_entry_archive = self.entry_id.is_entry_archive
            self.is_deferred_opportunities_archive = self.entry_id.is_deferred_opportunities_archive
            self.is_listing_archive_2023 = self.entry_id.is_listing_archive_2023
            self.is_technical_offers_archive = self.entry_id.is_technical_offers_archive
            self.is_partners_screen = self.entry_id.is_partners_screen

    @api.onchange('entry_p2_id')
    def _onchange_entry_p2_id(self):
        if self.entry_p2_id:
            self.request_type_id = self.entry_p2_id.request_type_id
            self.stage_id = self.entry_p2_id.stage_id
            self.is_move_to_direct_sales = self.entry_p2_id.is_move_to_direct_sales
            self.is_sale_cancelled = self.entry_p2_id.is_sale_cancelled
            self.is_sold = self.entry_p2_id.is_sold
            self.is_single_project = self.entry_p2_id.is_single_project

    def _delete_notification(self, target_name):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Deleted Successfully'),
                'message': _('The record "%s" has been permanently deleted.') % target_name,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _reset_stage_and_unlink(self, record, res_model):
        target_name = record.display_name or str(record.id)
        if hasattr(record, 'stage_id'):
            draft_stage = self.env['request.stage'].search(
                [('res_model', '=', res_model), ('state', '=', 'draft')],
                order='sequence asc', limit=1
            )
            if not draft_stage:
                draft_stage = self.env['request.stage'].search(
                    [('res_model', '=', res_model)],
                    order='sequence asc', limit=1
                )
                if draft_stage and draft_stage.state != 'draft':
                    draft_stage.sudo().write({'state': 'draft'})
            if draft_stage:
                record.sudo().write({'stage_id': draft_stage.id})
        record.sudo().unlink()
        return self._delete_notification(target_name)

    def action_delete_record(self):
        """Reset stage to draft, then permanently delete the selected record."""
        self.ensure_one()
        if self.control_type == 'phase1' and self.entry_id:
            return self._reset_stage_and_unlink(self.entry_id, 'entries')

        elif self.control_type == 'phase2' and self.entry_p2_id:
            return self._reset_stage_and_unlink(self.entry_p2_id, 'sales.auction.management')

        elif self.control_type == 'project':
            if not self.project_id:
                raise UserError(_("Please select a Project to delete."))
            return self._reset_stage_and_unlink(self.project_id, 'bussma.project')

        return {'type': 'ir.actions.act_window_close'}

    def action_confirm(self):
        self.ensure_one()

        if self.is_delete:
            return self.action_delete_record()

        res_model = ''
        res_id = 0
        if self.control_type == 'phase1' and self.entry_id:
            vals = {
                'stage_id': self.stage_id.id,
                'is_entry_archive': self.is_entry_archive,
                'is_deferred_opportunities_archive': self.is_deferred_opportunities_archive,
                'is_listing_archive_2023': self.is_listing_archive_2023,
                'is_technical_offers_archive': self.is_technical_offers_archive,
                'is_partners_screen': self.is_partners_screen,
                'requires_technical_offer': self.requires_technical_offer,
            }
            if self.project_path:
                vals['project_path'] = self.project_path
            if self.request_type_id:
                vals['request_type_id'] = self.request_type_id.id
            self.entry_id.write(vals)
            res_model = 'entries'
            res_id = self.entry_id.id
        elif self.control_type == 'phase2' and self.entry_p2_id:
            vals = {
                'stage_id': self.stage_id.id,
                'is_move_to_direct_sales': self.is_move_to_direct_sales,
                'is_sale_cancelled': self.is_sale_cancelled,
                'is_sold': self.is_sold,
                'is_single_project': self.is_single_project,
            }
            if self.request_type_id:
                vals['request_type_id'] = self.request_type_id.id
            self.entry_p2_id.write(vals)
            res_model = 'sales.auction.management'
            res_id = self.entry_p2_id.id
        elif self.control_type == 'menu' and self.menu_id:
            self.menu_id.write({'name': self.new_menu_name})
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        elif self.control_type == 'project' and self.project_id:
            res_model = 'bussma.project'
            res_id = self.project_id.id
        
        if res_model and res_id:
            return {
                'name': _('Record Control Redirect'),
                'type': 'ir.actions.act_window',
                'res_model': res_model,
                'res_id': res_id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {'type': 'ir.actions.act_window_close'}
