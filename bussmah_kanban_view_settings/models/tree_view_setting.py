# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TreeViewSetting(models.Model):
    _name = 'tree.view.setting'
    _description = 'Tree View Group Styling Setting'
    _order = 'model_name asc, id desc'
    _rec_name = 'display_name'

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
        domain=[('transient', '=', False)],
        help='Target model of the tree view',
    )
    model_name = fields.Char(
        string='Technical Model Name',
        related='model_id.model',
        store=True,
        readonly=True,
        index=True,
    )
    view_id = fields.Many2one(
        'ir.ui.view',
        string='Tree / List View',
        ondelete='cascade',
        domain="[('type', 'in', ['list', 'tree']), '|', ('model', '=', model_name), ('model', '=', False)]",
        help='Select a specific Tree/List view, or leave empty to apply to all tree views of this model',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this configuration is active',
    )
    # --- Column Headers Styling (thead th) ---
    col_header_bg_color = fields.Char(
        string='Column Header Background Color',
        default='#f8fafc',
        help='Background color for table column headers (thead th)',
    )
    col_header_text_color = fields.Char(
        string='Column Header Text Color',
        default='#334155',
        help='Text color for table column headers',
    )
    col_header_font_size = fields.Selection([
        ('11px', 'Extra Small (11px)'),
        ('12px', 'Small (12px)'),
        ('13px', 'Normal (13px - Standard)'),
        ('14px', 'Medium (14px)'),
        ('15px', 'Large (15px)'),
        ('16px', 'Extra Large (16px)'),
        ('18px', 'Huge (18px)'),
    ], string='Column Font Size', default='13px', required=True)
    col_header_font_bold = fields.Boolean(
        string='Bold Column Header Font',
        default=True,
    )
    col_header_font_family = fields.Char(
        string='Column Font Family',
        help='Optional custom font family (e.g. Cairo, Tajawal, Arial). Leave empty to use system default.',
    )
    col_header_hover_bg_color = fields.Char(
        string='Column Header Hover Background Color',
        default='#e2e8f0',
        help='Background color when hovering on column header',
    )

    # --- Grouped Headers Styling (o_group_header) ---
    group_bg_color = fields.Char(
        string='Group Header Background Color',
        default='#e2e8f0',
        help='Background color for group header rows',
    )
    group_text_color = fields.Char(
        string='Group Header Text Color',
        default='#0f172a',
        help='Text color for group header rows',
    )
    group_font_size = fields.Selection([
        ('14px', 'Medium (14px)'),
        ('15px', 'Large (15px - Recommended)'),
        ('16px', 'Extra Large (16px)'),
        ('18px', 'Huge (18px)'),
    ], string='Group Font Size', default='15px', required=True)
    group_font_bold = fields.Boolean(
        string='Bold Group Header Font',
        default=True,
    )
    group_font_family = fields.Char(
        string='Group Font Family',
        help='Optional custom font family (e.g. Cairo, Tajawal, Arial). Leave empty to use system default.',
    )
    group_hover_bg_color = fields.Char(
        string='Group Header Hover Background Color',
        default='#cbd5e1',
        help='Background color when hovering on group header',
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )

    @api.onchange('view_id')
    def _onchange_view_id(self):
        if self.view_id and self.view_id.model:
            model = self.env['ir.model'].search([('model', '=', self.view_id.model)], limit=1)
            if model:
                self.model_id = model

    @api.constrains('model_id', 'view_id')
    def _check_unique_view(self):
        for rec in self:
            domain = [
                ('id', '!=', rec.id),
                ('model_id', '=', rec.model_id.id),
                ('view_id', '=', rec.view_id.id if rec.view_id else False)
            ]
            if self.search_count(domain):
                raise ValidationError(_("A setting for this model and view already exists!"))

    @api.depends('model_id', 'model_id.name', 'model_name', 'view_id', 'view_id.name')
    def _compute_display_name(self):
        for rec in self:
            if rec.view_id:
                rec.display_name = f"{rec.view_id.name} [{rec.model_name}]"
            elif rec.model_id:
                rec.display_name = f"All Tree Views - {rec.model_id.name} [{rec.model_name}]"
            else:
                rec.display_name = _("New Tree View Setting")

    @api.model
    def get_tree_setting_for_view(self, model_name, view_id=None):
        """
        Find active setting for this view or model.
        Checks specific view_id first, then falls back to model-wide setting.
        """
        if not model_name:
            return False

        domain_base = [('model_name', '=', model_name), ('active', '=', True)]
        if view_id:
            setting = self.sudo().search(domain_base + [('view_id', '=', view_id)], limit=1)
            if setting:
                return setting

        return self.sudo().search(domain_base + [('view_id', '=', False)], limit=1)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self.env.registry.clear_cache()
        return records

    def write(self, vals):
        res = super().write(vals)
        self.env.registry.clear_cache()
        return res

    def unlink(self):
        res = super().unlink()
        self.env.registry.clear_cache()
        return res
