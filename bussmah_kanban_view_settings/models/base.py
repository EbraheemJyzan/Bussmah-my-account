# -*- coding: utf-8 -*-
from lxml import etree
from odoo import api, models


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        """
        Customize view loading (Kanban and List/Tree):
        1. Check if model is configured in kanban.view.setting:
        - If user is NOT authorized:
          * In Kanban: set can_open="0" (unless native kanban is already non-clickable).
          * In List/Tree: set no_open="1" and disable open_form_view="0".
        - If user IS authorized:
          * Leave original view rules intact.

        2. Check if tree view is configured in tree.view.setting:
        - In List/Tree: inject custom grouping header style attributes and class.
        """
        result = super().get_view(view_id=view_id, view_type=view_type, **options)

        if not self._name or not result.get('arch'):
            return result

        arch_modified = False
        arch_node = None

        if view_type in ('kanban', 'list'):
            # Detect action_id if available from options or context
            action_id = (
                options.get('action_id') or
                self.env.context.get('action') or
                self.env.context.get('params', {}).get('action')
            )
            # Check user permission to open records of this model (action-specific or model-wide)
            can_open = self.env['kanban.view.setting'].check_user_can_open_model(self._name, action_id=action_id)

            if not can_open:
                if arch_node is None:
                    arch_node = etree.fromstring(result['arch'])

                if view_type == 'kanban':
                    current_can_open = arch_node.get('can_open')
                    if current_can_open not in ('0', 'false', 'False'):
                        arch_node.set('can_open', '0')
                        arch_modified = True

                elif view_type == 'list':
                    current_no_open = arch_node.get('no_open')
                    if current_no_open not in ('1', 'true', 'True'):
                        arch_node.set('no_open', '1')
                        arch_modified = True
                    if arch_node.get('open_form_view') in ('1', 'true', 'True'):
                        arch_node.set('open_form_view', '0')
                        arch_modified = True

        if view_type == 'list':
            actual_view_id = view_id or result.get('id')
            setting = self.env['tree.view.setting'].get_tree_setting_for_view(self._name, actual_view_id)
            if setting:
                if arch_node is None:
                    arch_node = etree.fromstring(result['arch'])

                existing_class = arch_node.get('class', '')
                classes_to_add = []

                # Column headers styling
                has_col_styling = bool(
                    setting.col_header_bg_color
                    or setting.col_header_text_color
                    or setting.col_header_font_size
                    or setting.col_header_font_family
                )
                if has_col_styling and 'o_bussmah_col_header' not in existing_class:
                    classes_to_add.append('o_bussmah_col_header')

                # Group headers styling
                has_group_styling = bool(
                    setting.group_bg_color
                    or setting.group_text_color
                    or setting.group_font_size
                    or setting.group_font_family
                )
                if has_group_styling and 'o_bussmah_grouped_header' not in existing_class:
                    classes_to_add.append('o_bussmah_grouped_header')

                if classes_to_add:
                    arch_node.set('class', (existing_class + ' ' + ' '.join(classes_to_add)).strip())

                # Column Header attributes
                if has_col_styling:
                    if setting.col_header_bg_color:
                        arch_node.set('bussmah_col_header_bg', setting.col_header_bg_color)
                    if setting.col_header_text_color:
                        arch_node.set('bussmah_col_header_color', setting.col_header_text_color)
                    if setting.col_header_font_size:
                        arch_node.set('bussmah_col_header_size', setting.col_header_font_size)
                    arch_node.set('bussmah_col_header_bold', 'bold' if setting.col_header_font_bold else 'normal')
                    if setting.col_header_hover_bg_color:
                        arch_node.set('bussmah_col_header_hover_bg', setting.col_header_hover_bg_color)
                    if setting.col_header_font_family:
                        arch_node.set('bussmah_col_header_font', setting.col_header_font_family)

                # Group Header attributes
                if has_group_styling:
                    if setting.group_bg_color:
                        arch_node.set('bussmah_group_bg', setting.group_bg_color)
                    if setting.group_text_color:
                        arch_node.set('bussmah_group_color', setting.group_text_color)
                    if setting.group_font_size:
                        arch_node.set('bussmah_group_size', setting.group_font_size)
                    arch_node.set('bussmah_group_bold', 'bold' if setting.group_font_bold else 'normal')
                    if setting.group_hover_bg_color:
                        arch_node.set('bussmah_group_hover_bg', setting.group_hover_bg_color)
                    if setting.group_font_family:
                        arch_node.set('bussmah_group_font', setting.group_font_family)

                arch_modified = True

        if arch_modified and arch_node is not None:
            result['arch'] = etree.tostring(arch_node, encoding='unicode').replace('\t', '')

        return result
