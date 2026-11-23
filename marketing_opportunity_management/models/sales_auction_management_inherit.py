import logging
from collections import defaultdict
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class SalesAuctionManagementInherit(models.Model):
    _inherit = 'sales.auction.management'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(SalesAuctionManagementInherit, self).create(vals_list)
        m_rec_props = defaultdict(list)
        for rec in records:
            if rec.project_id:
                proj = rec.project_id
                m_rec = proj.marketing_id or self.env['bussma.marketing'].sudo().search([('bussma_project_id', '=', proj.id)], limit=1)
                if m_rec:
                    prop_name = rec.entrie_name or rec.display_name or _('Property')
                    m_rec_props[m_rec].append(prop_name)

        for m_rec, prop_names in m_rec_props.items():
            m_rec.sudo()._compute_sales_auction_ids()
            combined_names = ", ".join(filter(None, prop_names))
            m_rec.sudo()._send_property_changed_notification(action_type=_('Added'), property_name=combined_names, is_project=True)

        return records

    def write(self, vals):
        if 'project_id' in vals:
            old_projects = {rec.id: rec.project_id for rec in self}
            res = super(SalesAuctionManagementInherit, self).write(vals)
            new_project_id = vals.get('project_id')
            new_proj = self.env['bussma.project'].browse(new_project_id) if new_project_id else False

            old_m_rec_props = defaultdict(list)
            new_m_rec_props = defaultdict(list)

            for rec in self:
                old_proj = old_projects.get(rec.id)
                prop_name = rec.entrie_name or rec.display_name or _('Property')

                if old_proj and old_proj != new_proj:
                    old_m_rec = old_proj.marketing_id or self.env['bussma.marketing'].sudo().search([('bussma_project_id', '=', old_proj.id)], limit=1)
                    if old_m_rec:
                        old_m_rec_props[old_m_rec].append(prop_name)

                if new_proj and old_proj != new_proj:
                    new_m_rec = new_proj.marketing_id or self.env['bussma.marketing'].sudo().search([('bussma_project_id', '=', new_proj.id)], limit=1)
                    if new_m_rec:
                        new_m_rec_props[new_m_rec].append(prop_name)

            for old_m_rec, prop_names in old_m_rec_props.items():
                old_m_rec.sudo()._compute_sales_auction_ids()
                combined_names = ", ".join(filter(None, prop_names))
                old_m_rec.sudo()._send_property_changed_notification(action_type=_('Removed'), property_name=combined_names, is_project=True)

            for new_m_rec, prop_names in new_m_rec_props.items():
                new_m_rec.sudo()._compute_sales_auction_ids()
                combined_names = ", ".join(filter(None, prop_names))
                new_m_rec.sudo()._send_property_changed_notification(action_type=_('Added'), property_name=combined_names, is_project=True)

            return res
        return super(SalesAuctionManagementInherit, self).write(vals)

    def unlink(self):
        m_rec_props = defaultdict(list)
        for rec in self:
            if rec.project_id:
                proj = rec.project_id
                m_rec = proj.marketing_id or self.env['bussma.marketing'].sudo().search([('bussma_project_id', '=', proj.id)], limit=1)
                if m_rec:
                    prop_name = rec.entrie_name or rec.display_name or _('Property')
                    m_rec_props[m_rec].append(prop_name)

        res = super(SalesAuctionManagementInherit, self).unlink()

        for m_rec, prop_names in m_rec_props.items():
            m_rec.sudo()._compute_sales_auction_ids()
            combined_names = ", ".join(filter(None, prop_names))
            m_rec.sudo()._send_property_changed_notification(action_type=_('Removed'), property_name=combined_names, is_project=True)

        return res

