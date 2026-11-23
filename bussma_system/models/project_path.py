# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError

# Codes that must never be deleted
_PROTECTED_CODES = {
    'cities',
    'specialized',
    'standard',
}


class ProjectPath(models.Model):
    _name = 'project.path'
    _description = 'Project Path'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code')
    active = fields.Boolean(default=True)

    def _register_hook(self):
        super()._register_hook()
        self.env.cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'entries' AND column_name = 'project_path_rel'
        """)
        if self.env.cr.fetchone():
            self.env.cr.execute("""
                UPDATE entries e
                SET project_path_rel = p.id
                FROM project_path p
                WHERE e.project_path = p.code
                  AND e.project_path_rel IS NULL
                  AND e.project_path IS NOT NULL
            """)

    def unlink(self):
        protected = self.filtered(lambda r: r.code in _PROTECTED_CODES)
        if protected:
            raise UserError(_(
                "Can't delete protected records\n%s"
            ) % '\n'.join(f'- {r.name}' for r in protected))
        return super().unlink()
