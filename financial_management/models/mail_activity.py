# -*- coding: utf-8 -*-
from odoo import models, api

# Models for which activity completion/cancellation messages & activity creation emails should NOT appear / send
_SILENT_ACTIVITY_MODELS = {
    'entries',
    'financial.request',
    'bussma.marketing',
    'bussma.marketing.task',
    'bussma.marketing.material',
    'office.request',
    'sales.auction.management',
    'bussma.project',
    'bussma.opportunity',
    'hr.request',
    'hr.clearance.request',
}

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    @api.model_create_multi
    def create(self, vals_list):
        """Suppress automatic activity assignment emails for _SILENT_ACTIVITY_MODELS."""
        ctx = dict(self.env.context)
        for vals in vals_list:
            model = vals.get('res_model')
            if not model and vals.get('res_model_id'):
                model = self.env['ir.model'].sudo().browse(vals['res_model_id']).model
            if model in _SILENT_ACTIVITY_MODELS:
                ctx.update({
                    'mail_activity_quick_update': True,
                    'mail_create_nosubscribe': True,
                })
                break
        return super(MailActivity, self.with_context(ctx)).create(vals_list)

    def _log_activity_done(self):
        """Suppress 'To-Do done' / 'Cancelled' chatter messages for specific models."""
        silent = self.filtered(lambda a: a.res_model in _SILENT_ACTIVITY_MODELS)
        other = self - silent
        if other:
            return super(MailActivity, other)._log_activity_done()
        return self.env['mail.message']

    def action_done(self):
        """
        For specific models: silently delete the activity without posting any chatter message.
        For all other models: behave normally.
        """
        silent = self.filtered(lambda a: a.res_model in _SILENT_ACTIVITY_MODELS)
        other = self - silent

        # Delete silent activities directly without any log or message
        if silent:
            silent.sudo().with_context(force_delete=True).unlink()

        # Normal flow for other models
        if other:
            return super(MailActivity, other).action_done()

        return False

    def unlink(self):
        """Allow force_delete context to bypass any custom unlink restrictions."""
        return super().unlink()
