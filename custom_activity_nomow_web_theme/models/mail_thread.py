from odoo import models, api, _
from odoo.exceptions import AccessError

NO_FOLLOWER_MODELS = {
    'entries',
    'bussma.opportunity',
    'bussma.marketing',
    'bussma.marketing.task',
    'bussma.marketing.material',
    'office.request',
    'financial.request',
    'hr.request',
    'hr.clearance.request',
    'sales.auction.management',
    'bussma.project',
}


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def message_subscribe(self, partner_ids=None, subtype_ids=None):
        if self._name in NO_FOLLOWER_MODELS:
            return True
        return super(MailThread, self).message_subscribe(partner_ids=partner_ids, subtype_ids=subtype_ids)

    def _message_subscribe(self, partner_ids=None, subtype_ids=None, customer_ids=None):
        if self._name in NO_FOLLOWER_MODELS:
            return True
        return super(MailThread, self)._message_subscribe(partner_ids=partner_ids, subtype_ids=subtype_ids, customer_ids=customer_ids)

    def _message_auto_subscribe(self, updated_values, followers_existing_policy='skip'):
        if self._name in NO_FOLLOWER_MODELS:
            return True
        return super(MailThread, self)._message_auto_subscribe(updated_values, followers_existing_policy=followers_existing_policy)

    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        if self._name in NO_FOLLOWER_MODELS:
            return []
        return super(MailThread, self)._message_auto_subscribe_followers(updated_values, default_subtype_ids)

    def _check_can_update_message_content(self, messages):
        super()._check_can_update_message_content(messages)
        if not self.env.su:
            for message in messages:
                if message.model and message.model not in ('discuss.channel', 'mail.box'):
                    if not self.env.user.has_group('custom_activity_nomow_web_theme.group_record_editor'):
                        raise AccessError(_("You are not allowed to edit messages on this record."))


class MailFollowers(models.Model):
    _inherit = 'mail.followers'

    @api.model_create_multi
    def create(self, vals_list):
        filtered_vals = [vals for vals in vals_list if vals.get('res_model') not in NO_FOLLOWER_MODELS]
        if not filtered_vals:
            return self.browse()
        return super(MailFollowers, self).create(filtered_vals)

    def _insert_followers(self, res_model, res_ids, partner_ids, subtypes=None,
                          customer_ids=None, check_existing=True, existing_policy='skip'):
        if res_model in NO_FOLLOWER_MODELS:
            return
        return super(MailFollowers, self)._insert_followers(
            res_model, res_ids, partner_ids, subtypes=subtypes,
            customer_ids=customer_ids, check_existing=check_existing, existing_policy=existing_policy
        )
