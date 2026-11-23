# -*- coding: utf-8 -*-
from odoo import models, fields, api

class KwPartnerDuplicate(models.Model):
    _name = 'kw.partner.duplicate'
    _description = 'Partner Duplicates Group'

    mobile = fields.Char('Mobile Number', required=True, readonly=True)
    partner_ids = fields.Many2many('res.partner', string='Duplicate Partners', readonly=True)
    partners_count = fields.Integer('Duplicates Count', compute='_compute_partners_count')

    @api.depends('partner_ids')
    def _compute_partners_count(self):
        for rec in self:
            rec.partners_count = len(rec.partner_ids)

    def action_merge_manually(self):
        """ Allows the admin to merge this specific group manually from the UI """
        Wizard = self.env['base.partner.merge.automatic.wizard']
        for dup in self:
            if len(dup.partner_ids) > 1:
                # Keep the oldest record as the destination
                partners = dup.partner_ids.sorted(key=lambda p: p.id)
                dst_partner = partners[0]
                
                # Consolidate allowed_user_ids before merge
                all_uids = set()
                for p in partners:
                    all_uids.add(p.create_uid.id)
                    if hasattr(p, 'allowed_user_ids'):
                        all_uids.update(p.allowed_user_ids.ids)
                all_uids = [u for u in all_uids if u]
                if hasattr(dst_partner, 'allowed_user_ids'):
                    dst_partner.write({'allowed_user_ids': [(6, 0, all_uids)]})

                wizard = Wizard.create({
                    'state': 'selection',
                    'dst_partner_id': dst_partner.id,
                    'partner_ids': [(6, 0, dup.partner_ids.ids)],
                })
                # kw_partner_merge will execute this as SUPERUSER
                wizard.action_merge()
            # Remove the record from the duplicate tracking menu after merge
            dup.unlink()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.model
    def cron_find_duplicates(self):
        """ 
        Runs daily to find duplicate partners by applying dynamic regex normalization
        to catch duplicates regardless of spacing, hyphens, +966, 00966, or leading 0s.
        """
        self.env.cr.execute("""
            WITH normalized_partners AS (
                SELECT 
                    id, 
                    mobile,
                    REGEXP_REPLACE(
                        REGEXP_REPLACE(mobile, '[^0-9]', '', 'g'), 
                        '^(00966|966|0)+', 
                        ''
                    ) as norm_mobile
                FROM res_partner
                WHERE mobile IS NOT NULL AND mobile != '' AND active = true
            )
            SELECT norm_mobile, array_agg(id) as partner_ids
            FROM normalized_partners
            WHERE norm_mobile != ''
            GROUP BY norm_mobile
            HAVING COUNT(id) > 1
        """)
        duplicates = self.env.cr.dictfetchall()
        
        # Clear existing unmerged records to prevent clutter and outdated info
        self.search([]).unlink()

        for row in duplicates:
            self.create({
                'mobile': row['norm_mobile'],
                'partner_ids': [(6, 0, row['partner_ids'])],
            })

    @api.model
    def cron_merge_duplicates(self):
        """ 
        Runs weekly to automatically merge the populated duplicates.
        """
        duplicates = self.search([])
        Wizard = self.env['base.partner.merge.automatic.wizard']
        for dup in duplicates:
            if len(dup.partner_ids) > 1:
                partners = dup.partner_ids.sorted(key=lambda p: p.id)
                dst_partner = partners[0]
                
                # Consolidate allowed_user_ids before merge
                all_uids = set()
                for p in partners:
                    all_uids.add(p.create_uid.id)
                    if hasattr(p, 'allowed_user_ids'):
                        all_uids.update(p.allowed_user_ids.ids)
                all_uids = [u for u in all_uids if u]
                if hasattr(dst_partner, 'allowed_user_ids'):
                    dst_partner.write({'allowed_user_ids': [(6, 0, all_uids)]})

                wizard = Wizard.create({
                    'state': 'selection',
                    'dst_partner_id': dst_partner.id,
                    'partner_ids': [(6, 0, dup.partner_ids.ids)],
                })
                wizard.action_merge()
        
        # Clear the records after the automated merge completes
        duplicates.unlink()
