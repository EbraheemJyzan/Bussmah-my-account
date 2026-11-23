# -*- coding: utf-8 -*-
from odoo import models
from odoo.tools.safe_eval import safe_eval


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    def _get_action_dict(self):
        result = super()._get_action_dict()
        preliminary_act = self.env.ref('bussma_system.direct_sale_preliminary_study_action', raise_if_not_found=False)
        detailed_act = self.env.ref('bussma_system.direct_sale_detailed_study_action', raise_if_not_found=False)
        target_ids = {act.id for act in (preliminary_act, detailed_act) if act}

        if self.id in target_ids:
            is_comm_manager = self.env.user.has_group('bussma_system.group_commercial_sector_manager')
            ctx_str = result.get('context', '{}')
            try:
                ctx_dict = safe_eval(ctx_str) if isinstance(ctx_str, str) else dict(ctx_str or {})
            except Exception:
                ctx_dict = {}

            if is_comm_manager:
                ctx_dict['search_default_commercial_sector_stages'] = 1
                ctx_dict['search_default_project_stage'] = 1
            else:
                ctx_dict.pop('search_default_commercial_sector_stages', None)
                ctx_dict['search_default_project_stage'] = 1

            result['context'] = str(ctx_dict)

        return result
