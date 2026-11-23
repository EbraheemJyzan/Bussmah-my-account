# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class KanbanViewSetting(models.Model):
    _name = 'kanban.view.setting'
    _description = 'Kanban View Setting'
    _order = 'model_name asc'
    _rec_name = 'display_name'

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
        domain=[('transient', '=', False)],
        help='Target model to apply view settings on',
    )
    model_name = fields.Char(
        string='Technical Model Name',
        related='model_id.model',
        store=True,
        readonly=True,
        index=True,
    )
    is_action_specific = fields.Boolean(
        string='Specific Actions Only',
        default=False,
    )
    action_ids = fields.Many2many(
        'ir.actions.act_window',
        string='Window Actions',
        domain="[('res_model', '=', model_name)]",
    )
    group_ids = fields.Many2many(
        'res.groups',
        'kanban_view_setting_res_groups_rel',
        'setting_id',
        'group_id',
        string='Allowed Groups',
        help='User groups allowed to click and open records from Kanban or List view',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this configuration is active',
    )

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=False,
    )

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.action_ids = False

    @api.onchange('is_action_specific')
    def _onchange_is_action_specific(self):
        if not self.is_action_specific:
            self.action_ids = False

    @api.constrains('model_id', 'is_action_specific', 'action_ids')
    def _check_unique_model_actions(self):
        for rec in self:
            if not rec.is_action_specific:
                # General setting (applies to all actions): No other settings can exist for this model
                other_count = self.search_count([
                    ('id', '!=', rec.id),
                    ('model_id', '=', rec.model_id.id),
                ])
                if other_count:
                    raise ValidationError(
                        _("A setting already exists for model '%s'! When applying to all actions (entire model), no other settings can exist for this model.")
                        % rec.model_id.name
                    )
            else:
                if not rec.action_ids:
                    raise ValidationError(_("Please select at least one action when 'Specific Actions Only' is enabled!"))

                # 1. Prevent specific setting if a general setting already exists for this model
                general_exists = self.search_count([
                    ('id', '!=', rec.id),
                    ('model_id', '=', rec.model_id.id),
                    ('is_action_specific', '=', False),
                ])
                if general_exists:
                    raise ValidationError(
                        _("A general (all actions) setting already exists for model '%s'! You cannot create specific action settings unless the general setting is removed or made specific.")
                        % rec.model_id.name
                    )

                # 2. Prevent overlapping actions across specific settings for the same model
                conflicting = self.search([
                    ('id', '!=', rec.id),
                    ('model_id', '=', rec.model_id.id),
                    ('is_action_specific', '=', True),
                    ('action_ids', 'in', rec.action_ids.ids),
                ], limit=1)
                if conflicting:
                    overlapping = rec.action_ids & conflicting.action_ids
                    action_names = ", ".join(overlapping.mapped('name'))
                    raise ValidationError(
                        _("The action(s) '%s' are already configured in another setting for this model!")
                        % action_names
                    )

    @api.depends('model_id', 'model_name', 'is_action_specific')
    def _compute_display_name(self):
        for rec in self:
            if rec.model_id:
                if rec.is_action_specific and rec.action_ids:
                    action_part = f" -> {', '.join(rec.action_ids.mapped('name'))}"
                elif rec.is_action_specific:
                    action_part = " -> (No Actions Selected)"
                else:
                    action_part = " -> (All Actions)"
                rec.display_name = f"{rec.model_id.name} [{rec.model_name}]{action_part}"
            else:
                rec.display_name = _("New Setting")

    @api.model
    def check_user_can_open_model(self, model_name, user=None, action_id=None):
        """
        Check if the current user has permission to open records of this model in Kanban or List view.
        - If action_id is provided, check for setting containing this specific action in action_ids.
        - If no setting found for specific action, check for model-wide setting (model_name, is_action_specific=False).
        - If no active setting exists: allow opening (True).
        - If user is superuser or System Administrator (base.group_system): allow opening (True).
        - If an active setting exists:
            * If allowed groups are defined: check if user belongs to any of them.
            * If no groups defined: only System Administrators can open (False).
        """
        if not model_name:
            return True

        user = user or self.env.user
        if self.env.is_superuser() or user.has_group('base.group_system'):
            return True

        action_int = None
        if action_id:
            if isinstance(action_id, int):
                action_int = action_id
            elif isinstance(action_id, str) and action_id.isdigit():
                action_int = int(action_id)

        setting = None
        if action_int:
            setting = self.sudo().search([
                ('model_name', '=', model_name),
                ('is_action_specific', '=', True),
                ('action_ids', 'in', [action_int]),
                ('active', '=', True)
            ], limit=1)

        if not setting:
            setting = self.sudo().search([
                ('model_name', '=', model_name),
                ('is_action_specific', '=', False),
                ('active', '=', True)
            ], limit=1)

        if not setting:
            return True

        if not setting.group_ids:
            return False

        user_groups = set(user.groups_id.ids)
        allowed_groups = set(setting.group_ids.ids)
        return bool(user_groups & allowed_groups)

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
