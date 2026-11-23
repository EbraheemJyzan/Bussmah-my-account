# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import io
import ast
import xlsxwriter
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PowerbiControllers(http.Controller):

    @http.route("/get/reportparameter", auth="user", type="json")
    def get_report_parameter(self, res_id, **kw):
        reportObj = request.env['powerbi.report'].browse(res_id)
        data = {}
        if reportObj:
            resp = reportObj.get_report()
            data = {'embed_url': resp.get('embed_url'), 'embed_token': resp.get(
                'embed_token'), 'token_expiry': resp.get('token_expiry')}
        return data

    @http.route("/get/dashboardparameter", auth="user", type="json")
    def get_dashboard_parameter(self, res_id, **kw):
        dashboardObj = request.env['powerbi.dashboard'].browse(res_id)
        data = {}
        if dashboardObj:
            resp = dashboardObj.get_dashboard()
            data = {'embed_url': resp.get('embed_url'), 'embed_token': resp.get(
                'embed_token'), 'token_expiry': resp.get('token_expiry')}
        return data

    @http.route("/odoo_connect/instance/<int:instance_id>", type="http", auth="user")
    def odoo_connect(self, instance_id, **kw):
        connectionObj = request.env["powerbi.connection"].browse(instance_id)
        if connectionObj and kw.get('code'):
            connectionObj.write({
                'state': 'connected',
                'status': "Test connection successful, now you can proceed with synchronization!!",
                'connection_status': True
            })
        action_id = request.env.ref(
            'odoo_powerbi_connect.powerbi_connection_tree_action').id
        url = f"/odoo/action-{action_id}/{connectionObj.id}"
        return request.redirect(url)

    @http.route("/powerbi_dataset/<int:dataset_id>", type="http", auth="bearer")
    def powerbi_dataset(self, dataset_id, **kw):
        dataset = request.env["powerbi.dataset"].search(
            [('id', '=', dataset_id), ('is_published', '=', True)])
        try:
            page = max(int(kw.get('page', 1)), 1)
        except Exception:
            _logger.warning("Invalid page '%s', defaulting to 1", kw.get('page'))
            page = 1
        if dataset:
            output = self._prepare_workbook(dataset, page, is_public=False)
            status = 200
            headers = [
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition',
                f'inline; filename="{dataset.name}.xlsx"'),
            ]
        else:
            output = "Requested dataset not found."
            status = 404
            headers = None
        return request.make_response(output, headers=headers, status=status)

    @http.route("/powerbi_dataset/<int:dataset_id>/web/<string:web_token>", type="http", auth="public")
    def powerbi_dataset_web(self, dataset_id, web_token, **kw):
        dataset = request.env["powerbi.dataset"].sudo().search(
            [('id', '=', dataset_id), ('is_published', '=', True)])
        status, output, headers = 200, "", None
        try:
            page = max(int(kw.get('page', 1)), 1)
        except Exception:
            _logger.warning("Invalid page '%s', defaulting to 1", kw.get('page'))
            page = 1
        if dataset:
            if dataset.web_token != web_token:
                status = 403

            if status == 200:
                output = self._prepare_workbook(dataset, page)
                headers = [
                    ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    ('Content-Disposition',
                    f'inline; filename="{dataset.name}.xlsx"'),
                ]
        else:
            output = "Requested dataset not found."
            status = 404

        return request.make_response(output, headers=headers, status=status)

    def _prepare_workbook(self, dataset, page, is_public=True):
        io_file = io.BytesIO()
        workbook = xlsxwriter.Workbook(io_file, {'in_memory': True})
        connObj = request.env['powerbi.connection'].sudo(
        ).get_active_connection()
        tz = connObj.wk_time_zone
        for table in dataset.table_ids:
            model = request.env[table.model_id.model]
            if is_public:
                model = model.sudo()

            domain = []
            if table.filter_domain:
                domain = ast.literal_eval(table.filter_domain)
            offset = (page - 1) * table.page_size
            records = model.search_fetch(
                domain, table.column_ids.mapped('name'), offset=offset, limit=table.page_size)

            field_list = [(records._fields[field.name], field.label)
                          for field in table.column_ids]

            worksheet = workbook.add_worksheet(table.name)
            column_format = workbook.add_format({
                'bold': True,
            })
            # ID included by default
            worksheet.write(0, 0, 'ID', column_format)
            for col_num, column in enumerate(field_list, start=1):
                worksheet.write(0, col_num, column[1], column_format)

            row_num = 1
            use_relation = table.use_relation
            for rec in records.with_context(tz=tz):
                for key, value in self.get_row_data(rec, field_list, use_relation).items():
                    worksheet.write(row_num, key, value)
                row_num += 1

        workbook.close()
        return io_file.getvalue()

    def get_row_data(self, dataObj, field_list, use_relation):
        row = {0: dataObj['id']}
        for index, field in enumerate(field_list, start=1):
            field_rec = field[0]
            value = dataObj[field_rec.name]
            if field_rec.type == 'many2one':
                if use_relation:
                    row[index] = value and value['id'] or ""
                else:
                    row[index] = value['display_name']
            elif field_rec.type == 'many2many':
                if value:
                    m2m_data = ', '.join(value.mapped('display_name'))
                    row[index] = m2m_data
            elif field_rec.type == 'datetime':
                row[index] = field_rec.convert_to_display_name(value, dataObj)
            else:
                row[index] = value or '' if field_rec.type in [
                    'date'] else value
        return row
