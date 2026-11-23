# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


# Codes that must never be deleted
_PROTECTED_CODES = {
    'committee_decision_accepted',
    'committee_decision_rejected',
    'request_transfer_auction',
}


class AuctionManagerApproval(models.Model):
    _name = 'auction.manager.approval'
    _description = 'Auction Manager Approval'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code')
    active = fields.Boolean(default=True)

    def unlink(self):
        protected = self.filtered(lambda r: r.code in _PROTECTED_CODES)
        if protected:
            raise UserError(_(
                "Can't delete protected records\n%s"
            ) % '\n'.join(f'- {r.name}' for r in protected))
        return super().unlink()
