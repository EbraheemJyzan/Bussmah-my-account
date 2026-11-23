from odoo import _, api, models
from odoo.exceptions import ValidationError


class ResUsersRole(models.Model):
    _inherit = "res.users.role"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # check if user add groups to role
            model = (self.sudo() if self._bypass_rules() else self).browse()
            if not vals.get("implied_ids", False):
                raise ValidationError(_("You must add at least one group"))
        return super(ResUsersRole, model).create(vals_list)

    def write(self, vals):
        recs = self.sudo() if self._bypass_rules() else self
        # check if user add groups to role
        # odoo previous format [[6, False, [68]]] new format [[4,id]] for link  and [[3,id]] for delete
        res = super(ResUsersRole, recs).write(vals)
        for rec in recs:
            if not rec.implied_ids:
                raise ValidationError(_("The role must have at least one group"))
        return res
