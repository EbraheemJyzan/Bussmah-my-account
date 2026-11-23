from odoo import models, api


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def _filter_visible_menus(self):
        visible_menus = super()._filter_visible_menus()
        user = self.env.user

        if self.env.su or user.has_group('base.group_system'):
            return visible_menus

        # 1. Must have Real Tech Portfolio App group
        if not user.has_group('real_tech_portfolio_app.group_real_tech_portfolios_app'):
            return visible_menus

        # 2. Check if user has ANY group from the specified 4 modules
        modules_to_check = (
            'bussma_system.',
            'marketing_opportunity_management.',
            'sales_and_auction_management.',
        )

        group_xml_ids = user.groups_id.get_external_id().values()

        has_module_group = any(
            xml_id.startswith(modules_to_check) and
            xml_id != 'real_tech_portfolio_app.group_real_tech_portfolios_app'
            for xml_id in group_xml_ids
        )

        if has_module_group:
            return visible_menus

        target_root_menus = [
            'bussma_system.rout_menu_commercial_sector',
            'marketing_opportunity_management.menu_opportunity_root',
            'marketing_opportunity_management.menu_marketing_root',
            'marketing_opportunity_management.menu_office_request_root',
            'sales_and_auction_management.menu_employee_guide_root',
            'sales_and_auction_management.menu_sales_management_root',
            'sales_and_auction_management.menu_auctions_management_root',
        ]

        menus_to_hide = self.env['ir.ui.menu']
        for xml_id in target_root_menus:
            menu_rec = self.env.ref(xml_id, raise_if_not_found=False)
            if menu_rec and menu_rec in visible_menus:
                menus_to_hide |= menu_rec

        return visible_menus - menus_to_hide
