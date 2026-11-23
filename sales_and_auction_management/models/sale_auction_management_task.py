# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectTask(models.Model):
    _name = 'project.task'
    _description = 'Project Task'
    _order = 'id desc'

    entry_id = fields.Many2one('sales.auction.management', string="Property/Project", ondelete='cascade', required=True)
    name = fields.Char(string="Task Name", required=True)
    user_id = fields.Many2one('res.users', string="Executor", required=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    task_attachments = fields.Many2many(
        'ir.attachment',
        'entries_phase2_task_task_attachments_rel',
        'task_id',
        'attachment_id',
        string="Attachments"
    )
    response = fields.Text(string="Response Area")
    is_completed = fields.Boolean(string="Completed")
    completion_attachments = fields.Many2many(
        'ir.attachment',
        'entries_phase2_task_completion_attachments_rel',
        'task_id',
        'attachment_id',
        string="Completion Attachments")

    @api.model_create_multi
    def create(self, vals_list):
        # 1. Access validation for create
        for vals in vals_list:
            entry = self.env['sales.auction.management'].browse(vals.get('entry_id'))
            if entry and not self.env.su:
                # ONLY Project Manager can create tasks
                if entry.project_manager_id and self.env.user != entry.project_manager_id:
                    raise UserError(_("Sorry, only the project manager (%s) is authorized to create tasks.") % entry.project_manager_id.name)
        
        # 2. Create the records
        records = super(ProjectTask, self).create(vals_list)
        # 3. Rename attachments and send notifications
        records._rename_attachments()
        # records._send_assignment_notification()
        return records

    def write(self, vals):
        # 1. Access validation for write
        is_admin = self.env.su or self.env.user.has_group('base.group_system')
        # Fields that only the assignee (user_id) can fill
        assignee_fields = {'response', 'is_completed', 'completion_attachments'}
        modified_assignee_fields = assignee_fields.intersection(vals.keys())
        # Fields that only the Project Manager (entry_id.project_manager_id) can edit
        pm_fields = {'name', 'user_id', 'start_date', 'end_date', 'task_attachments'}
        modified_pm_fields = pm_fields.intersection(vals.keys())
        for rec in self:
            # if not is_admin:
            # Assignee fields restriction
            if modified_assignee_fields:
                if self.env.user != rec.user_id:
                    raise UserError(_("Sorry, only the executor (%s) is authorized to fill or modify these fields: %s") % (rec.user_id.name, ", ".join(modified_assignee_fields)))
            # PM fields restriction
            if modified_pm_fields:
                if rec.entry_id.project_manager_id and self.env.user != rec.entry_id.project_manager_id:
                    raise UserError(_("Sorry, only the project manager (%s) is authorized to modify these fields: %s") % (rec.entry_id.project_manager_id.name, ", ".join(modified_pm_fields)))
        # 2. Check if user_id or name is changed to send notification
        old_assignees = {rec.id: rec.user_id.id for rec in self}
        # 3. Perform write
        res = super(ProjectTask, self).write(vals)
        # 4. Trigger rename of attachments and send new notifications if assignee or details changed
        self._rename_attachments()
        return res

    def unlink(self):
        for rec in self:
            if not self.env.su and not self.env.user.has_group('base.group_system'):
                if rec.entry_id.project_manager_id and self.env.user != rec.entry_id.project_manager_id:
                    raise UserError(_("Sorry, only the project manager (%s) is authorized to delete tasks.") % rec.entry_id.project_manager_id.name)
        return super(ProjectTask, self).unlink()

    def _rename_attachments(self):
        for rec in self:
            if rec.entry_id and rec.entry_id.entrie_name:
                prefix = rec.entry_id.entrie_name
                # Rename task_attachments
                for att in rec.task_attachments:
                    if att.name and prefix not in att.name:
                        att.sudo().write({'name': f"{prefix} - {att.name}"})
                # Rename completion_attachments
                for att in rec.completion_attachments:
                    if att.name and prefix not in att.name:
                        att.sudo().write({'name': f"{prefix} - {att.name}"})
