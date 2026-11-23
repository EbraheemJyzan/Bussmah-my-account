# -*- coding: utf-8 -*-
from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def get_entries_activity_counts(self):
        """
        Returns a dictionary mapping menu xmlid (and menu id)
        to the count of records that have pending activities 
        (Today or Overdue) for the current user matching standard Odoo filters.
        """
        user = self.env.user
        today = fields.Date.today()
        result = {}

        # --- 1. ENTRIES MODEL ACTIVITIES ---
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'entries'),
            ('user_id', '=', user.id),
            ('date_deadline', '<=', today)
        ])
        entry_ids = list(set(activities.mapped('res_id')))
        if entry_ids:
            entries_domain = [('id', 'in', entry_ids)]
            actions = self.env['ir.actions.act_window'].search([('res_model', '=', 'entries')])
            menus = self.env['ir.ui.menu'].search([('action', 'like', 'ir.actions.act_window,')])
            
            eval_context = {
                'ref': lambda xmlid: self.env.ref(xmlid, raise_if_not_found=False).id if self.env.ref(xmlid, raise_if_not_found=False) else False,
                'user': user,
                'uid': user.id,
            }

            total_entries_count = len(entry_ids)
            result['bussma_system.rout_menu_commercial_sector'] = total_entries_count

            for action in actions:
                combined_domain = list(entries_domain)
                if action.domain:
                    try:
                        domain_str = action.domain
                        if isinstance(domain_str, str):
                            eval_domain = eval(domain_str, eval_context)
                        else:
                            eval_domain = domain_str
                        if isinstance(eval_domain, list):
                            combined_domain = entries_domain + eval_domain
                    except Exception as e:
                        _logger.warning("Error evaluating domain for action %s: %s", action.name, e)

                count = self.env['entries'].search_count(combined_domain)
                if count > 0:
                    action_ref = f"ir.actions.act_window,{action.id}"
                    action_menus = menus.filtered(lambda m: m.action == action or str(m.action) == action_ref)
                    for m in action_menus:
                        xmlid = m.get_external_id().get(m.id)
                        if xmlid:
                            result[xmlid] = count
                        result[str(m.id)] = count

                        parent = m.parent_id
                        while parent:
                            parent_xmlid = parent.get_external_id().get(parent.id)
                            if parent_xmlid:
                                result[parent_xmlid] = result.get(parent_xmlid, 0) + count
                            result[str(parent.id)] = result.get(str(parent.id), 0) + count
                            parent = parent.parent_id

        # --- 2. MARKETING MANAGEMENT ACTIVITIES (ROOT MENU ONLY) ---
        mkt_models = ['bussma.marketing', 'bussma.marketing.material', 'bussma.marketing.task']
        mkt_activities = self.env['mail.activity'].search([
            ('res_model', 'in', mkt_models),
            ('user_id', '=', user.id),
            ('date_deadline', '<=', today)
        ])
        
        mat_act_ids = set(mkt_activities.filtered(lambda a: a.res_model == 'bussma.marketing.material').mapped('res_id'))
        task_act_ids = set(mkt_activities.filtered(lambda a: a.res_model == 'bussma.marketing.task').mapped('res_id'))
        mkt_act_ids = set(mkt_activities.filtered(lambda a: a.res_model == 'bussma.marketing').mapped('res_id'))

        total_marketing_count = len(mat_act_ids) + len(task_act_ids) + len(mkt_act_ids)

        if total_marketing_count > 0:
            result['marketing_opportunity_management.menu_marketing_root'] = total_marketing_count

        # --- 3. FINANCIAL MANAGEMENT ACTIVITIES ---
        fin_activities = self.env['mail.activity'].search([
            ('res_model', '=', 'financial.request'),
            ('user_id', '=', user.id),
            ('date_deadline', '<=', today)
        ])
        fin_req_ids = list(set(fin_activities.mapped('res_id')))
        if fin_req_ids:
            total_financial_count = len(fin_req_ids)

            fin_domain = [('id', 'in', fin_req_ids)]
            actions = self.env['ir.actions.act_window'].search([('res_model', '=', 'financial.request')])
            menus = self.env['ir.ui.menu'].search([('action', 'like', 'ir.actions.act_window,')])

            eval_context = {
                'ref': lambda xmlid: self.env.ref(xmlid, raise_if_not_found=False).id if self.env.ref(xmlid, raise_if_not_found=False) else False,
                'user': user,
                'uid': user.id,
            }

            for action in actions:
                combined_domain = list(fin_domain)
                if action.domain:
                    try:
                        domain_str = action.domain
                        if isinstance(domain_str, str):
                            eval_domain = eval(domain_str, eval_context)
                        else:
                            eval_domain = domain_str
                        if isinstance(eval_domain, list):
                            combined_domain = fin_domain + eval_domain
                    except Exception as e:
                        _logger.warning("Error evaluating domain for financial action %s: %s", action.name, e)

                count = self.env['financial.request'].search_count(combined_domain)
                if count > 0:
                    action_ref = f"ir.actions.act_window,{action.id}"
                    action_menus = menus.filtered(lambda m: m.action == action or str(m.action) == action_ref)
                    for m in action_menus:
                        xmlid = m.get_external_id().get(m.id)
                        if xmlid:
                            result[xmlid] = count
                        result[str(m.id)] = count

                        parent = m.parent_id
                        while parent:
                            parent_xmlid = parent.get_external_id().get(parent.id)
                            if parent_xmlid:
                                result[parent_xmlid] = result.get(parent_xmlid, 0) + count
                            result[str(parent.id)] = result.get(str(parent.id), 0) + count
                            parent = parent.parent_id

            result['financial_management.menu_financial_management_root'] = total_financial_count

        # --- 4. HR REQUESTS ACTIVITIES ---
        hr_activities = self.env['mail.activity'].search([
            ('res_model', '=', 'hr.request'),
            ('user_id', '=', user.id),
            ('date_deadline', '<=', today)
        ])
        hr_req_ids = list(set(hr_activities.mapped('res_id')))
        if hr_req_ids:
            total_hr_count = len(hr_req_ids)

            hr_domain = [('id', 'in', hr_req_ids)]
            actions = self.env['ir.actions.act_window'].search([('res_model', '=', 'hr.request')])
            menus = self.env['ir.ui.menu'].search([('action', 'like', 'ir.actions.act_window,')])

            eval_context = {
                'ref': lambda xmlid: self.env.ref(xmlid, raise_if_not_found=False).id if self.env.ref(xmlid, raise_if_not_found=False) else False,
                'user': user,
                'uid': user.id,
            }

            for action in actions:
                combined_domain = list(hr_domain)
                if action.domain:
                    try:
                        domain_str = action.domain
                        if isinstance(domain_str, str):
                            eval_domain = eval(domain_str, eval_context)
                        else:
                            eval_domain = domain_str
                        if isinstance(eval_domain, list):
                            combined_domain = hr_domain + eval_domain
                    except Exception as e:
                        _logger.warning("Error evaluating domain for HR action %s: %s", action.name, e)

                count = self.env['hr.request'].search_count(combined_domain)
                if count > 0:
                    action_ref = f"ir.actions.act_window,{action.id}"
                    action_menus = menus.filtered(lambda m: m.action == action or str(m.action) == action_ref)
                    for m in action_menus:
                        xmlid = m.get_external_id().get(m.id)
                        if xmlid:
                            result[xmlid] = count
                        result[str(m.id)] = count

                        parent = m.parent_id
                        while parent:
                            parent_xmlid = parent.get_external_id().get(parent.id)
                            if parent_xmlid:
                                result[parent_xmlid] = result.get(parent_xmlid, 0) + count
                            result[str(parent.id)] = result.get(str(parent.id), 0) + count
                            parent = parent.parent_id

            result['hr_requests.menu_hr_request_main'] = total_hr_count

        # --- 4.5. OFFICE REQUESTS ACTIVITIES ---
        off_activities = self.env['mail.activity'].search([
            ('res_model', '=', 'office.request'),
            ('user_id', '=', user.id),
            ('date_deadline', '<=', today)
        ])
        off_req_ids = list(set(off_activities.mapped('res_id')))
        if off_req_ids:
            total_off_count = len(off_req_ids)

            off_domain = [('id', 'in', off_req_ids)]
            actions = self.env['ir.actions.act_window'].search([('res_model', '=', 'office.request')])
            menus = self.env['ir.ui.menu'].search([('action', 'like', 'ir.actions.act_window,')])

            eval_context = {
                'ref': lambda xmlid: self.env.ref(xmlid, raise_if_not_found=False).id if self.env.ref(xmlid, raise_if_not_found=False) else False,
                'user': user,
                'uid': user.id,
            }

            for action in actions:
                combined_domain = list(off_domain)
                if action.domain:
                    try:
                        domain_str = action.domain
                        if isinstance(domain_str, str):
                            eval_domain = eval(domain_str, eval_context)
                        else:
                            eval_domain = domain_str
                        if isinstance(eval_domain, list):
                            combined_domain = off_domain + eval_domain
                    except Exception as e:
                        _logger.warning("Error evaluating domain for Office Request action %s: %s", action.name, e)

                count = self.env['office.request'].search_count(combined_domain)
                if count > 0:
                    action_ref = f"ir.actions.act_window,{action.id}"
                    action_menus = menus.filtered(lambda m: m.action == action or str(m.action) == action_ref)
                    for m in action_menus:
                        xmlid = m.get_external_id().get(m.id)
                        if xmlid:
                            result[xmlid] = count
                        result[str(m.id)] = count

                        parent = m.parent_id
                        while parent:
                            parent_xmlid = parent.get_external_id().get(parent.id)
                            if parent_xmlid:
                                result[parent_xmlid] = result.get(parent_xmlid, 0) + count
                            result[str(parent.id)] = result.get(str(parent.id), 0) + count
                            parent = parent.parent_id

            result['marketing_opportunity_management.menu_office_request_list'] = total_off_count

        # --- 5. OPPORTUNITY MANAGEMENT ACTIVITIES ---
        opp_activities = self.env['mail.activity'].search([
            ('res_model', '=', 'bussma.opportunity'),
            ('user_id', '=', user.id),
            ('date_deadline', '<=', today)
        ])
        opp_ids = list(set(opp_activities.mapped('res_id')))
        if opp_ids:
            total_opp_count = len(opp_ids)
            result['marketing_opportunity_management.menu_opportunity_root'] = total_opp_count

        # Exclude Employee Guide root menu from showing activity badge counts
        emp_guide_menu = self.env.ref('sales_and_auction_management.menu_employee_guide_root', raise_if_not_found=False)
        if emp_guide_menu:
            result.pop(str(emp_guide_menu.id), None)
        result.pop('sales_and_auction_management.menu_employee_guide_root', None)

        return result
