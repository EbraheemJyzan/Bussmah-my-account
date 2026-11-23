from odoo import models, api


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def _filter_visible_menus(self):
        visible_menus = super()._filter_visible_menus()
        user = self.env.user

        # Superuser, System Admins, and Marketing Supervisors can see all department menus
        if self.env.su or user.has_group('marketing_opportunity_management.group_marketing_supervisor'):
            return visible_menus

        dept_menu_xml_map = {
            'marketing_opportunity_management.menu_marketing_material_content': 'CONTENT',
            'marketing_opportunity_management.menu_marketing_material_design': 'DESIGN',
            'marketing_opportunity_management.menu_marketing_material_digital': 'DIGITAL',
            'marketing_opportunity_management.menu_marketing_material_ops': 'OPS',
        }

        # Find active departments where user is either manager or member
        user_depts = self.env['bussma.marketing.department'].sudo().search([
            ('active', '=', True),
            '|', ('manager_id', '=', user.id), ('member_ids', 'in', user.id)
        ])
        user_dept_codes = set(user_depts.mapped(lambda d: d.code.upper() if d.code else ''))

        menus_to_hide = self.env['ir.ui.menu']
        for xml_id, code in dept_menu_xml_map.items():
            menu_rec = self.env.ref(xml_id, raise_if_not_found=False)
            if menu_rec and menu_rec in visible_menus:
                if code not in user_dept_codes:
                    menus_to_hide |= menu_rec

        filtered_menus = visible_menus - menus_to_hide

        # Handle parent menu 'Departments' (menu_marketing_departments_root)
        parent_menu = self.env.ref('marketing_opportunity_management.menu_marketing_departments_root', raise_if_not_found=False)
        if parent_menu and parent_menu in filtered_menus:
            child_dept_menus = self.env['ir.ui.menu']
            for xml_id in dept_menu_xml_map.keys():
                m = self.env.ref(xml_id, raise_if_not_found=False)
                if m:
                    child_dept_menus |= m
            # If user has no access to any of the department submenus, hide parent menu
            if not (filtered_menus & child_dept_menus):
                filtered_menus -= parent_menu

        return filtered_menus