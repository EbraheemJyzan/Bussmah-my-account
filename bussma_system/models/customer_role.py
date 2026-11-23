# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError

# Codes that must never be deleted
_PROTECTED_CODES = {
    'owner',
    'agent',
    'broker',
    'other',
}


class CustomerRole(models.Model):
    _name = 'customer.role'
    _description = 'Customer Role'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code')
    active = fields.Boolean(default=True)

    def _register_hook(self):
        super()._register_hook()
        self.env.cr.execute("""
            SELECT count(*) 
            FROM information_schema.columns 
            WHERE table_name = 'entries' AND column_name IN ('customer_role_rel', 'customer_role')
        """)
        res = self.env.cr.fetchone()
        if res and res[0] == 2:
            self.env.cr.execute("""
                UPDATE entries e
                SET customer_role_rel = r.id
                FROM customer_role r
                WHERE e.customer_role = r.code
                  AND e.customer_role_rel IS NULL
                  AND e.customer_role IS NOT NULL
            """)

    def unlink(self):
        protected = self.filtered(lambda r: r.code in _PROTECTED_CODES)
        if protected:
            raise UserError(_(
                "Can't delete protected records\n%s"
            ) % '\n'.join(f'- {r.name}' for r in protected))
        return super().unlink()
