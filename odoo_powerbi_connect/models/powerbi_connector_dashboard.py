# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import json
import logging
from odoo import fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import timedelta
from babel.dates import format_date, format_datetime

_logger = logging.getLogger(__name__)


class PowerbiConnectorDashboard(models.Model):
    _name = "powerbi.connector.dashboard"
    _description = "PowerBI Connector Dashboard"

    color = fields.Integer(string='Color Index', default=6)
    name = fields.Char(string="Name", default='Workspace')
    state = fields.Selection(
        [('eventhouse', 'Eventhouse'), ('database', 'KQL Database'), ('dataset', 'Dataset'), ('workspace', 'Workspace'), ('report', 'Report'), ('table', 'Table'), ('dashboard', 'Dashboard')])
    total_count = fields.Integer(compute="_total_count")
    publish_count = fields.Integer(compute="_publish_count")
    unpublish_count = fields.Integer(compute="_unpublish_count")
    kanban_dashboard_graph_data = fields.Text(
        compute='_kanban_dashboard_graph_data')

    def total_data(self):
        '''This method Used To Redirect Total Data Of selected Models '''
        for rec in self:
            if rec.state == "eventhouse":
                model_name = 'powerbi.eventhouse'
            if rec.state == "database":
                model_name = 'powerbi.kql.database'
            if rec.state == "dataset":
                model_name = 'powerbi.dataset'
            if rec.state == "workspace":
                model_name = 'powerbi.workspace'
            if rec.state == "table":
                model_name = 'powerbi.table'
            if rec.state == "report":
                model_name = 'powerbi.report'
            if rec.state == "dashboard":
                model_name = 'powerbi.dashboard'
            return {
                "type": "ir.actions.act_window",
                'name': rec.name,
                'res_model': model_name,
                'view_mode': 'list,form',
                'target': 'current'
            }

    def _total_count(self):
        '''This method Used To Count Total Data Of Models '''
        for rec in self:
            if rec.state == 'eventhouse':
                rec.total_count = self.env['powerbi.eventhouse'].search_count(
                    [])

            if rec.state == 'database':
                rec.total_count = self.env['powerbi.kql.database'].search_count(
                    [])

            if rec.state == 'dataset':
                rec.total_count = self.env['powerbi.dataset'].search_count(
                    [])

            if rec.state == 'workspace':
                rec.total_count = self.env['powerbi.workspace'].search_count(
                    [])

            if rec.state == 'table':
                rec.total_count = self.env['powerbi.table'].search_count(
                    [])

            if rec.state == 'report':
                rec.total_count = self.env['powerbi.report'].search_count(
                    [])

            if rec.state == 'dashboard':
                rec.total_count = self.env['powerbi.dashboard'].search_count(
                    [])

    def _publish_count(self):
        '''This method Used To Count Total Publish Data Models '''
        for rec in self:
            if rec.state == 'eventhouse':
                rec.publish_count = self.env['powerbi.eventhouse'].search_count(
                    [('is_published', '=', True)])

            if rec.state == 'database':
                rec.publish_count = self.env['powerbi.kql.database'].search_count(
                    [('is_published', '=', True)])

            if rec.state == 'dataset':
                rec.publish_count = self.env['powerbi.dataset'].search_count(
                    [('is_published', '=', True)])

            if rec.state == 'workspace':
                rec.publish_count = self.env['powerbi.workspace'].search_count(
                    [('is_published', '=', True)])

            if rec.state == 'table':
                rec.publish_count = self.env['powerbi.table'].search_count(
                    [('is_published', '=', True)])

            if rec.state == 'report':
                rec.publish_count = 0

            if rec.state == 'dashboard':
                rec.publish_count = 0

    def _unpublish_count(self):
        '''This method Used To Count Total UnPublish Data Models '''
        for rec in self:
            if rec.state == 'eventhouse':
                rec.unpublish_count = self.env['powerbi.eventhouse'].search_count(
                    [('is_published', '=', False)])

            if rec.state == 'database':
                rec.unpublish_count = self.env['powerbi.kql.database'].search_count(
                    [('is_published', '=', False)])

            if rec.state == 'dataset':
                rec.unpublish_count = self.env['powerbi.dataset'].search_count(
                    [('is_published', '=', False)])

            if rec.state == 'workspace':
                rec.unpublish_count = self.env['powerbi.workspace'].search_count(
                    [('is_published', '=', False)])

            if rec.state == 'table':
                rec.unpublish_count = self.env['powerbi.table'].search_count(
                    [('is_published', '=', False)])

            if rec.state == 'report':
                rec.unpublish_count = 0

            if rec.state == 'dashboard':
                rec.unpublish_count = 0

    def action_create_new(self):
        '''This method is used to create a new corresponding record.'''
        if self.state == "eventhouse":
            model_name = 'powerbi.eventhouse'
        if self.state == "database":
            model_name = 'powerbi.kql.database'
        if self.state == "dataset":
            model_name = 'powerbi.dataset'
        if self.state == "workspace":
            model_name = 'powerbi.workspace'
        if self.state == "table":
            model_name = 'powerbi.table'
        if self.state == "report":
            model_name = 'powerbi.report'
        if self.state == "dashboard":
            model_name = 'powerbi.dashboard'
        return {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": model_name,
            "view_mode": "form",
            "target": "current"
        }

    def action_unpublish(self):
        '''This method Used To Redirect Unpublish Data Of selected Models '''
        for rec in self:
            if rec.state == "eventhouse":
                model_name = 'powerbi.eventhouse'
            if rec.state == "database":
                model_name = 'powerbi.kql.database'
            if rec.state == "dataset":
                model_name = 'powerbi.dataset'
            if rec.state == "workspace":
                model_name = 'powerbi.workspace'
            if rec.state == "table":
                model_name = 'powerbi.table'
            if rec.state == "report":
                model_name = 'powerbi.report'
            if rec.state == "dashboard":
                model_name = 'powerbi.dashboard'
            return {
                "type": "ir.actions.act_window",
                'name': rec.name,
                'res_model': model_name,
                'domain': [('is_published', '=', False)],
                'view_mode': 'list,form',
                'target': 'current'
            }

    def action_publish(self):
        '''This method Used To Redirect Publish Data Of selected Models '''
        for rec in self:
            if rec.state == "eventhouse":
                model_name = 'powerbi.eventhouse'
            if rec.state == "database":
                model_name = 'powerbi.kql.database'
            if rec.state == "dataset":
                model_name = 'powerbi.dataset'
            if rec.state == "workspace":
                model_name = 'powerbi.workspace'
            if rec.state == "table":
                model_name = 'powerbi.table'
            if rec.state == "report":
                model_name = 'powerbi.report'
            if rec.state == "dashboard":
                model_name = 'powerbi.dashboard'
            return {
                "type": "ir.actions.act_window",
                'name': rec.name,
                'res_model': model_name,
                'domain': [('is_published', '=', True)],
                'view_mode': 'list,form',
                'target': 'current'
            }

    def _kanban_dashboard_graph_data(self):
        for record in self:
            if record.state == 'workspace':
                record.kanban_dashboard_graph_data = json.dumps(
                    record.get_bar_graph_datas('powerbi_workspace'))
            if record.state == 'eventhouse':
                record.kanban_dashboard_graph_data = json.dumps(
                    record.get_bar_graph_datas('powerbi_eventhouse'))
            if record.state == 'database':
                record.kanban_dashboard_graph_data = json.dumps(
                    record.get_bar_graph_datas('powerbi_kql_database'))
            if record.state == 'dataset':
                record.kanban_dashboard_graph_data = json.dumps(
                    record.get_bar_graph_datas('powerbi_dataset'))
            if record.state == 'table':
                record.kanban_dashboard_graph_data = json.dumps(
                    record.get_bar_graph_datas('powerbi_table'))
            if record.state == 'report':
                record.kanban_dashboard_graph_data = json.dumps(
                    record.get_bar_graph_datas('powerbi_report'))
            if record.state == 'dashboard':
                record.kanban_dashboard_graph_data = json.dumps(
                    record.get_bar_graph_datas('powerbi_dashboard'))

    def get_bar_graph_datas(self, modelName):
        self.ensure_one()
        data = []
        allowed_models = {'powerbi_workspace': 'Workspaces', 'powerbi_eventhouse': 'Eventhouses',
                          'powerbi_kql_database': 'KQL Databases', 'powerbi_dataset': 'Datasets',
                          'powerbi_table': 'Tables', 'powerbi_report': 'Reports', 'powerbi_dashboard': 'Dashboards'}

        try:
            if modelName not in allowed_models:
                raise Exception(
                    f"model '{modelName}' is not a valid model to generate graph data.")

            fecthDate = 'create_date'
            today = fields.Date.context_today(self)
            data.append({'label': _('Past'), 'value': 0.0, 'type': 'past'})
            locale = self._context.get('lang', 'en_US')
            day_of_week = int(
                format_datetime(
                    today,
                    'e',
                    locale=locale))
            first_day_of_week = today + timedelta(days=-day_of_week + 1)
            for i in range(-1, 1):
                if i == 0:
                    label = _('This Week')
                    typ = 'future'
                else:
                    start_week = first_day_of_week + timedelta(days=i * 7)
                    end_week = start_week + timedelta(days=6)
                    if start_week.month == end_week.month:
                        label = str(start_week.day) + '-' + str(end_week.day) + ' ' + format_date(
                            end_week, 'MMM', locale=locale)
                    else:
                        label = format_date(start_week, 'd MMM', locale=locale) \
                            + '-' \
                            + format_date(end_week, 'd MMM',
                                          locale=locale)
                    typ = 'present'
                data.append({'label': label, 'value': 0.0, 'type': typ})

            # Build SQL query to find amount aggregated by week
            select_sql_clause = """SELECT COUNT(*) as total FROM """+modelName

            query = ''
            start_date = (first_day_of_week + timedelta(days=-7))
            for i in range(0, 3):
                if i == 0:
                    query += "(" + (select_sql_clause) + " where " + \
                        fecthDate + " < '" + start_date.strftime(DF) + "')"
                else:
                    next_date = start_date + timedelta(days=7)
                    query += " UNION ALL (" + (select_sql_clause) + " where " + fecthDate + " >= '" + start_date.strftime(
                        DF) + "' and " + fecthDate + " < '" + next_date.strftime(DF) + "')"
                    start_date = next_date

            self.env.cr.execute(query)
            query_results = self.env.cr.dictfetchall()
            for index in range(0, len(query_results)):
                total = str(query_results[index].get('total'))
                total = total.split('L')
                if int(total[0]) > 0:
                    data[index]['value'] = total[0]
        except Exception as e:
            _logger.info(f"### Exception during graph data creation: {str(e)}")
        finally:
            color = '#3e1e5e'
            graphData = [{'values': data, 'area': True,
                          'title': '', 'key': allowed_models.get(modelName), 'color': color}]
            return graphData
