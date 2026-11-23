# -*- coding: utf-8 -*-
from odoo import models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def action_merge_duplicates_by_mobile(self):
        """
        Finds all partners with the same mobile number and merges them.
        Uses the base.partner.merge.automatic.wizard to handle the merging safely
        with SUPERUSER permissions from kw_partner_merge.
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
        
        if not duplicates:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'لا يوجد مكررات',
                    'message': 'لم يتم العثور على عملاء مكررين بنفس رقم الجوال.',
                    'type': 'info',
                    'sticky': False,
                }
            }

        Wizard = self.env['base.partner.merge.automatic.wizard']
        for row in duplicates:
            partner_ids = row['partner_ids']
            partners = self.env['res.partner'].browse(partner_ids).sorted(key=lambda p: p.id)
            if len(partners) > 1:
                dst_partner = partners[0]
                
                # [MODIFIED] Collect all users who created or were allowed on any of the duplicates
                # This ensures the master record is visible to everyone who added this mobile number.
                all_uids = set()
                for p in partners:
                    all_uids.add(p.create_uid.id)
                    if hasattr(p, 'allowed_user_ids'):
                        all_uids.update(p.allowed_user_ids.ids)
                
                # Filter out False values if any
                all_uids = [u for u in all_uids if u]
                if hasattr(dst_partner, 'allowed_user_ids'):
                    dst_partner.write({'allowed_user_ids': [(6, 0, all_uids)]})

                wizard = Wizard.create({
                    'state': 'selection',
                    'dst_partner_id': dst_partner.id,
                    'partner_ids': [(6, 0, partner_ids)],
                })
                # kw_partner_merge will execute this as SUPERUSER
                wizard.action_merge()
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'تمت العملية بنجاح',
                'message': 'تم الانتهاء من دمج كافة الشركاء المكررين بناءً على رقم الجوال.',
                'type': 'success',
                'sticky': False,
            }
        }
