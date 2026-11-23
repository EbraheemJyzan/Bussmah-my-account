from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import test_python_expr

class RequestStage(models.Model):
    _inherit = 'request.stage'

    project_stage_selection = fields.Selection([
        ('entry_screen', 'Entry Screen'),
        ('data_completion', 'Data Completion'),
        ('define_project_path_assign_analyst', 'Define Project Path'),
        ('analyst', 'Preliminary Study Analyst'),
        ('study_approval', 'Preliminary Study Approval'),
        ('detailed_study_analyst', 'Detailed Study Analyst'),
        ('detailed_study_approval', 'Detailed Study Approval'),
        ('committee_decision', 'Committee Decision'),
        ('sales_manager_decision', 'Sales Manager Decision'),
        ('auctions_manager_decision', 'Auctions Manager Decision'),
        ('commercial_manager_approval', 'Commercial Manager Approval'),
        ('assign_negotiator', 'Assign Negotiator'),
        ('negotiator', 'Negotiator'),
        ('deputy_studies_manager_approval', 'Deputy Studies Manager Approval'),
        ('manager_contract_approval', 'Manager Contract Approval'),
        ('contract_followup', 'Contract Followup'),
        ('negotiation_approval', 'Negotiation Approval'),
        ('contract_completion', 'Contract Completion'),
        ('completed', 'Completed'),
        ('city_study_analyst', 'Study Analyst'),
        ('city_study_approval', 'Study Approval'),
        ('city_study_completed', 'City Study - Completed'),
    ], string='Project Stage Selection')
    color = fields.Integer(string='Color')


    @api.constrains("code", "project_stage_selection")
    def _check_python_code(self):
        # Original logic for code check
        for action in self.sudo().filtered("code"):
            msg = test_python_expr(expr=action.code.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)
            
        # New uniqueness condition for project_stage_selection
        for record in self:
            if record.project_stage_selection:
                duplicate = self.search([
                    ('id', '!=', record.id),
                    ('project_stage_selection', '=', record.project_stage_selection)
                ], limit=1)
                if duplicate:
                    selection_label = dict(self._fields['project_stage_selection'].selection).get(record.project_stage_selection)
                    raise ValidationError(_("The Project Stage Selection '%s' is already assigned to another stage (%s). It must be unique.") % (selection_label, duplicate.name))
