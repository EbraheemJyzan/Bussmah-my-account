import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class BussmaMarketing(models.Model):
    _name = 'bussma.marketing'
    _description = 'Marketing Management'
    _inherit = 'request'
    _order = 'id desc'

    def _default_stage_id(self):
        req_type = self.env.ref('marketing_opportunity_management.request_type_marketing', raise_if_not_found=False)
        if req_type:
            return self.env['request.stage'].search([('request_type_ids', 'in', req_type.id)], order='sequence asc', limit=1)
        return False

    @api.model
    def _read_group_stage_ids(self, stages, domain=None, order=None):
        req_type = self.env.ref('marketing_opportunity_management.request_type_marketing', raise_if_not_found=False)
        if req_type:
            return self.env['request.stage'].search([('request_type_ids', 'in', req_type.id)], order='sequence asc')
        return self.env['request.stage'].search([('res_model', '=', 'bussma.marketing')], order='sequence asc')

    request_type_id = fields.Many2one(
        'request.type',
        string='Request Type',
        default=lambda self: self.env.ref('marketing_opportunity_management.request_type_marketing', raise_if_not_found=False)
    )
    stage_id = fields.Many2one(
        'request.stage',
        string='Stage',
        default=_default_stage_id,
        group_expand='_read_group_stage_ids',
        domain="[('res_model', '=', 'bussma.marketing')]",
        tracking=True
    )
    active = fields.Boolean(default=True)
    marketing_stage_selection = fields.Selection(
        related='stage_id.marketing_stage_selection',
        string='Stage for Fields',
        store=True
    )
    is_marketing_supervisor = fields.Boolean(
        string='Is Marketing Supervisor',
        compute='_compute_is_marketing_supervisor'
    )
    project_status = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], string='Project Status', compute='_compute_project_status', store=True, tracking=True)
    is_opportunity_request = fields.Boolean(string='Is Opportunity Request', default=False)
    is_office_request = fields.Boolean(string='Is Office Request', default=False)
    request_type_category = fields.Selection([
        ('opportunity', 'Opportunity Request'),
        ('project', 'Project Request'),
        ('office', 'Department Request'),
    ], string='Request Category', compute='_compute_request_type_category', store=True, tracking=True)

    source_request_type_name = fields.Char(
        string='Source Request Type Name',
        compute='_compute_source_request_type_name',
        store=True
    )
    office_department_id = fields.Many2one('office.department', string='Department', tracking=True)
    requested_by_id = fields.Many2one('res.users', string='Requested By', tracking=True)
    code = fields.Char(string='Code', readonly=True, copy=False, default='/')
    name = fields.Char(
        string='Project Name',
        compute='_compute_name',
        store=True,
        readonly=False,
        precompute=True,
        tracking=True
    )
    material_responsible_id = fields.Many2one('res.users', string='Marketing Material Responsible', tracking=True)
    user_id = fields.Many2one('res.users', string='Marketing Record Supervisor', default=lambda self: self.env.user, tracking=True)
    opportunity_id = fields.Many2one('bussma.opportunity', string='Related Opportunity', tracking=True)
    office_request_id = fields.Many2one('office.request', string='Related Office Request', tracking=True)
    office_request_type = fields.Selection([
        ('id_card', 'ID Card'),
        ('business_card', 'Business Card'),
        ('email_signature', 'Email Signature'),
        ('signboard_design', 'Signboard Design'),
        ('design_request', 'Design Request'),
        ('internal_communication', 'Internal Communication'),
        ('project_request', 'Project'),
        ('change_request', 'Change Request'),
        ('thank_you_certificate', 'Thank You Certificate'),
        ('other', 'Other'),
    ], string='Office Request Type', tracking=True)
    employee_name = fields.Char(string='Employee Name', tracking=True)
    job_title = fields.Char(string='Job Title', tracking=True)
    employee_number = fields.Char(string='Employee Number', tracking=True)
    employee_email = fields.Char(string='Employee Email', tracking=True)
    phone_number = fields.Char(string='Phone Number', tracking=True)
    extension_number = fields.Char(string='Extension Number', tracking=True)
    region_id = fields.Many2one('res.country.state', string='Region', domain="[('country_id.code', '=', 'SA')]", tracking=True)
    property_code = fields.Char(string='Property Code', tracking=True)
    signboard_size = fields.Char(string='Signboard Size', tracking=True)
    needs_identity = fields.Boolean(string='Needs Identity?', tracking=True)
    needs_content_writing = fields.Boolean(string='Needs Content Writing?', tracking=True)
    request_description = fields.Text(string='Request Details Description', tracking=True)

    # Project Request Fields
    project_name = fields.Char(string='Project Name', tracking=True)
    project_type_selection = fields.Selection([
        ('sales', 'Direct Sale'),
        ('auction_pvt', 'Private Auction'),
        ('auction_enf', 'Enforcement Auction'),
        ('city', 'Cities'),
        ('other', 'Other'),
    ], string='Project Type', tracking=True)
    has_proposed_project_name = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Has Proposed Project Name?', tracking=True)
    proposed_project_name = fields.Char(string='Proposed Project Name', tracking=True)
    is_masterplan = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Is Project a Masterplan/Scheme?', tracking=True)
    # Change Request Fields
    change_request_type = fields.Selection([
        ('add_property', 'Add Property'),
        ('remove_property', 'Remove Property'),
        ('other', 'Other'),
    ], string='Change Request Type', tracking=True)
    target_marketing_project_id = fields.Many2one('bussma.marketing', string='Target Marketing Project to Edit', tracking=True)
    # Shared New Fields
    delivery_date = fields.Date(string='Delivery Date', tracking=True)
    has_attachments = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Has Attachments?', tracking=True)
    bussma_project_id = fields.Many2one('bussma.project', string='Related Project', tracking=True)
    project_cat = fields.Selection(
        related='bussma_project_id.project_cat',
        string='Project Category',
        readonly=True,
        store=True,
    )
    sales_auction_ids = fields.Many2many(
        'sales.auction.management',
        'bussma_marketing_sales_auction_rel',
        'marketing_id',
        'sales_id',
        string='Related Properties',
        compute='_compute_sales_auction_ids',
        store=True,
        readonly=False,
        tracking=True
    )
    entry_ids = fields.Many2many('entries', 'bussma_marketing_entries_rel', 'marketing_id', 'entry_id', string='Opportunity Properties', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Client', related='opportunity_id.partner_id', store=True, readonly=False)
    property_name = fields.Char(string='Property Name', tracking=True)
    opportunity_type = fields.Selection([
        ('commercial_lease', 'Commercial Lease'),
        ('property_sale', 'Property Sale'),
        ('investment', 'Investment'),
        ('development', 'Development')
    ], string='Opportunity Type', tracking=True)
    source = fields.Selection([
        ('system', 'System (Automatic)'),
        ('email', 'Email'),
        ('website', 'Website'),
        ('external_source', 'External Source'),
    ], string='Source', default='system', tracking=True)
    opportunity_source = fields.Selection([
        ('system', 'Studies System'),
        ('email', 'Email'),
        ('etimad', 'Etimad Platform'),
        ('forsa', 'Forsa Platform'),
        ('iskan', 'Housing Platform'),
        ('entifa', 'Entifa Platform'),
        ('sec', 'Saudi Electricity Company Platform'),
        ('external_source', 'Other'),
    ], string='Source', tracking=True)
    source_other = fields.Char(string='Other Source', tracking=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Priority', tracking=True)
    client_requirements = fields.Text(string='Client Requirements', tracking=True)
    project_status_sales = fields.Selection([
        ('under_development', 'Under Development'),
        ('ready_for_sale', 'Ready for Sale'),
        ('on_map', 'On Map'),
        ('under_construction', 'Under Construction'),
    ], string='Project Status', tracking=True)
    contract_status = fields.Selection([
        ('negotiating', 'Negotiating'),
        ('contracted', 'Contracted'),
        ('on_hold', 'On Hold'),
    ], string='Contract Status', tracking=True)
    city_id = fields.Many2one('res.country.state', string='City', domain="[('country_id.code', '=', 'SA'), ('code', 'ilike', 'CT_')]", tracking=True)
    district_id = fields.Many2one('res.city', string='District', domain="[('state_id', '=', city_id)]", tracking=True)
    property_type_id = fields.Many2one('property.type', string='Property Type', tracking=True)
    area_sqm = fields.Float(string='Area (sqm)', tracking=True)
    sale_price = fields.Float(string='Sale Price', tracking=True)
    department_ids = fields.Many2many(
        'bussma.marketing.department',
        'bussma_marketing_dept_rel',
        'marketing_id',
        'dept_id',
        string='Departments',
        tracking=True
    )
    marketing_activity_ids = fields.Many2many(
        'bussma.marketing.activity',
        'bussma_marketing_activity_rel',
        'marketing_id',
        'activity_id',
        string='Marketing Activities'
    )
    marketing_activity_domain = fields.Char(
        string='Marketing Activity Domain',
        compute='_compute_marketing_activity_domain',
    )
    material_ids = fields.Many2many(
        'bussma.marketing.material',
        'bussma_marketing_material_rel',
        'marketing_id',
        'material_id',
        string='Marketing Materials'
    )
    material_backup_ids = fields.Many2many(
        'bussma.marketing.material',
        'bussma_marketing_material_backup_rel',
        'marketing_id',
        'material_id',
        string='Backup Marketing Materials'
    )
    material_count = fields.Integer(string='Marketing Materials Count', compute='_compute_material_count')
    return_to_requester_notes = fields.Text(string='Return to Requester Notes', tracking=True)
    attachment_return_ids = fields.Many2many(
        'ir.attachment',
        'bussma_marketing_return_attachment_rel',
        'mkt_id',
        'attachment_id',
        string='Return Attachments'
    )
    is_returned_to_requester = fields.Boolean(string='Request Returned to Requester', default=False)
    start_date = fields.Date(string='Start Date', default=fields.Date.context_today)
    end_date = fields.Date(string='End Date')
    budget = fields.Float(string='Budget')
    attachments_request_ids = fields.Many2many(
        'ir.attachment',
        'bussma_marketing_attachments_request_rel',
        'mkt_id',
        'att_id',
        string='Request Attachments'
    )
    notes = fields.Text(string='Request Requirements / Notes', tracking=True)
    row_id_notes = fields.Char(string="Row ID")

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields=allfields, attributes=attributes)
        if res and 'active' in res:
            res['active']['readonly'] = True
            res['active']['invisible'] = True
        return res

    def _get_source_code_from_vals(self, vals, rec=None):
        source_code = False
        bussma_project_id = vals.get('bussma_project_id') or (rec.bussma_project_id.id if rec and rec.bussma_project_id else False)
        opportunity_id = vals.get('opportunity_id') or (rec.opportunity_id.id if rec and rec.opportunity_id else False)
        office_department_id = vals.get('office_department_id') or (rec.office_department_id.id if rec and rec.office_department_id else False)
        office_request_id = vals.get('office_request_id') or (rec.office_request_id.id if rec and rec.office_request_id else False)
        # 1. From Project
        if bussma_project_id:
            proj = self.env['bussma.project'].browse(bussma_project_id)
            if proj.exists() and proj.code:
                source_code = proj.code

        # 2. From Opportunity
        if not source_code and opportunity_id:
            opp = self.env['bussma.opportunity'].browse(opportunity_id)
            if opp.exists() and opp.code:
                source_code = opp.code

        # 3. From Internal Department / Office Request
        if not source_code and office_department_id:
            dept = self.env['office.department'].browse(office_department_id)
            if dept.exists() and dept.code:
                source_code = dept.code

        if not source_code and office_request_id:
            off_req = self.env['office.request'].browse(office_request_id)
            if off_req.exists():
                if off_req.department_id and off_req.department_id.code:
                    source_code = off_req.department_id.code
                elif off_req.code and off_req.code != '/':
                    source_code = off_req.code

        return source_code

    @api.onchange('bussma_project_id', 'opportunity_id', 'office_department_id', 'office_request_id')
    def _onchange_source_code(self):
        for rec in self:
            source_code = self._get_source_code_from_vals({}, rec=rec)
            if source_code:
                rec.code = source_code

    @api.onchange('opportunity_id')
    def _onchange_opportunity_id_entries(self):
        for rec in self:
            if rec.opportunity_id and rec.opportunity_id.entry_ids:
                rec.entry_ids = [(6, 0, rec.opportunity_id.entry_ids.ids)]

    @api.depends('opportunity_id', 'is_opportunity_request')
    def _compute_marketing_activity_domain(self):
        # Codes for offer-type activities (opportunity-only)
        offer_codes = ['ACT0010', 'ACT0011', 'ACT0012']
        # Aerial photo code (for opportunity)
        aerial_code = 'ACT0004'

        # Get IDs for the offer activities
        offer_activities = self.env['bussma.marketing.activity'].search([
            ('code', 'in', offer_codes)
        ])
        aerial_activity = self.env['bussma.marketing.activity'].search([
            ('code', '=', aerial_code)
        ], limit=1)

        opportunity_activity_ids = aerial_activity.ids + offer_activities.ids
        non_opportunity_excluded_ids = offer_activities.ids

        for rec in self:
            if rec.is_opportunity_request or rec.opportunity_id:
                # From opportunity: show only aerial photo + 3 offer activities
                if opportunity_activity_ids:
                    rec.marketing_activity_domain = str([('id', 'in', opportunity_activity_ids)])
                else:
                    rec.marketing_activity_domain = str([('id', 'in', [])])
            else:
                # From another department: exclude the 3 offer activities
                if non_opportunity_excluded_ids:
                    rec.marketing_activity_domain = str([('id', 'not in', non_opportunity_excluded_ids)])
                else:
                    rec.marketing_activity_domain = str([])

    @api.depends('bussma_project_id', 'bussma_project_id.name')
    def _compute_name(self):
        for rec in self:
            if rec.bussma_project_id:
                rec.name = rec.bussma_project_id.name
            else:
                rec.name = rec.name

    @api.depends('is_opportunity_request', 'is_office_request', 'opportunity_id', 'office_request_id', 'office_department_id', 'bussma_project_id')
    def _compute_source_request_type_name(self):
        for rec in self:
            if rec.is_opportunity_request or rec.opportunity_id:
                rec.source_request_type_name = _('Opportunity Management')
            elif rec.bussma_project_id:
                rec.source_request_type_name = _("Project Request")
            elif rec.is_office_request or rec.office_request_id or rec.office_department_id:
                rec.source_request_type_name = _("Department Request")
            else:
                rec.source_request_type_name = False

    @api.depends('is_opportunity_request', 'is_office_request', 'opportunity_id', 'bussma_project_id', 'office_request_id')
    def _compute_request_type_category(self):
        for rec in self:
            if rec.is_opportunity_request or rec.opportunity_id:
                rec.request_type_category = 'opportunity'
            elif rec.bussma_project_id:
                rec.request_type_category = 'project'
            elif rec.is_office_request or rec.office_request_id:
                rec.request_type_category = 'office'
            else:
                rec.request_type_category = 'opportunity'

    @api.depends('bussma_project_id')
    def _compute_sales_auction_ids(self):
        for rec in self:
            if rec.bussma_project_id:
                props = self.env['sales.auction.management'].search([('project_id', '=', rec.bussma_project_id.id)])
                rec.sales_auction_ids = [(6, 0, props.ids)]
            elif not rec.sales_auction_ids:
                rec.sales_auction_ids = [(5, 0, 0)]

    @api.depends('stage_id', 'marketing_stage_selection')
    def _compute_project_status(self):
        for rec in self:
            stage_sel = rec.marketing_stage_selection
            if stage_sel == 'mkt_draft':
                rec.project_status = 'new'
            elif stage_sel in ('mkt_review', 'mkt_approval'):
                rec.project_status = 'in_progress'
            elif stage_sel == 'mkt_done':
                rec.project_status = 'done'
            else:
                rec.project_status = False

    @api.depends_context('uid')
    def _compute_is_marketing_supervisor(self):
        is_sup = self.env.user.has_group('marketing_opportunity_management.group_marketing_supervisor') or self.env.su
        for rec in self:
            rec.is_marketing_supervisor = is_sup

    def _check_marketing_supervisor_permission(self):
        user = self.env.user
        if not user.has_group('marketing_opportunity_management.group_marketing_supervisor'):
            raise UserError(_("Sorry, this action is only for marketing supervisor."))

    def action_open_return_to_opportunity_wizard(self):
        self.ensure_one()
        self._check_marketing_supervisor_permission()
        return {
            'name': _('Return to Requester'),
            'type': 'ir.actions.act_window',
            'res_model': 'marketing.return.to.requste.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_marketing_id': self.id,
            }
        }

    @api.depends('name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name

    def action_send_for_review_and_classification(self):
        self._check_marketing_supervisor_permission()
        stage = self.env.ref('marketing_opportunity_management.stage_marketing_review', raise_if_not_found=False)
        for rec in self:
            if stage:
                rec.write({'stage_id': stage.id})
                rec._onchange_stage_id()

    def action_send_for_marketing_supervisor_approval(self):
        self._check_marketing_supervisor_permission()
        stage = self.env.ref('marketing_opportunity_management.stage_marketing_supervisor_approval', raise_if_not_found=False)
        for rec in self:
            if stage:
                rec.write({'stage_id': stage.id})
                rec._onchange_stage_id()

    def action_send_to_done(self):
        self._check_marketing_supervisor_permission()
        stage = self.env.ref('marketing_opportunity_management.stage_marketing_done', raise_if_not_found=False)
        for rec in self:
            if rec.material_ids:
                uncompleted_materials = rec.material_ids.filtered(lambda m: m.material_stage_selection != 'mat_done')
                if uncompleted_materials:
                    material_names = ", ".join(uncompleted_materials.mapped('name'))
                    if rec.bussma_project_id:
                        raise UserError(_("The marketing request cannot be moved to completed because the following materials have not been approved and completed by the project manager:\n%s") % material_names)
                    else:
                        raise UserError(_("Due to \n%s \nmaterials not completed, the request cannot be moved to done.") % material_names)

            if stage:
                rec.write({'stage_id': stage.id})
                rec._onchange_stage_id()
            if rec.opportunity_id:
                rec.opportunity_id._send_opportunity_mail_template('marketing_opportunity_management.email_template_opportunity_final_material_sent')
                # ─ Create internal activity notification for opportunity managers ─
                opp = rec.opportunity_id
                opp._create_opportunity_activity(
                    summary='final_material: %s' % (opp.code or ''),
                    note=_(
                        "The final deliverable for marketing request number <b>%s</b> associated with opportunity <b>%s</b> has been sent. Please review the deliverables."
                    ) % (rec.code or '', opp.code or '')
                )
            if rec.office_request_id:
                rec.office_request_id.write({
                    'state': 'done',
                })

    my_activity_count = fields.Integer(
        string="My Activity Count",
        compute="_compute_my_activity_count"
    )

    @api.depends('material_ids')
    def _compute_material_count(self):
        for record in self:
            record.material_count = len(record.material_ids)

    @api.depends_context('uid')
    @api.depends(
        'material_ids',
        'material_ids.activity_ids',
        'material_ids.activity_ids.user_id',
        'material_ids.task_ids',
        'material_ids.task_ids.activity_ids',
        'material_ids.task_ids.activity_ids.user_id'
    )
    def _compute_my_activity_count(self):
        current_user = self.env.user
        for record in self:
            materials = record.material_ids
            tasks = materials.mapped('task_ids')

            mat_act_count = sum(1 for m in materials if any(act.user_id == current_user for act in m.activity_ids))
            task_act_count = sum(1 for t in tasks if any(act.user_id == current_user for act in t.activity_ids))

            record.my_activity_count = mat_act_count + task_act_count

    def action_view_materials(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Marketing Materials'),
            'res_model': 'bussma.marketing.material',
            'view_mode': 'kanban,list,form',
            'domain': [('marketing_id', '=', self.id), ('id', 'in', self.material_ids.ids), ('material_stage_selection', '!=', 'mat_done')],
            'context': {
                'default_marketing_id': self.id,
                'search_default_group_by_department': 1,
            }
        }

    def action_view_materials_done(self):
        self.ensure_one()
        stage = self.env.ref('marketing_opportunity_management.stage_mat_done', raise_if_not_found=False)
        domain = [('marketing_id', '=', self.id), ('id', 'in', self.material_ids.ids)]
        if stage:
            domain.append(('stage_id', '=', stage.id))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Marketing Materials'),
            'res_model': 'bussma.marketing.material',
            'view_mode': 'kanban,list,form',
            'domain': domain,
            'context': {
                'default_marketing_id': self.id,
            }
        }

    def _sync_materials_from_activities(self):
        Material = self.env['bussma.marketing.material']
        req_type = self.env.ref('marketing_opportunity_management.request_type_marketing_material', raise_if_not_found=False)
        stage = self.env.ref('marketing_opportunity_management.stage_mat_content_exec', raise_if_not_found=False) \
            or self.env['request.stage'].search([('res_model', '=', 'bussma.marketing.material')], order='sequence asc', limit=1)

        for record in self:
            selected_activities = record.marketing_activity_ids
            current_mats = record.material_ids
            backup_mats = record.material_backup_ids

            mats_to_add = []
            backup_to_add = []

            for activity in selected_activities:
                has_active = any(
                    m.activity_id == activity or (m.code and activity.code and m.code == activity.code)
                    for m in current_mats
                )
                if not has_active:
                    match = next((
                        b for b in backup_mats
                        if b.activity_id == activity or (b.code and activity.code and b.code == activity.code)
                    ), None)
                    if match:
                        mats_to_add.append(match.id)
                    else:
                        new_mat = Material.create({
                            'name': activity.name or 'Marketing Material',
                            'code': activity.code,
                            'activity_id': activity.id,
                            'department_ids': [(6, 0, activity.department_ids.ids)],
                            'marketing_id': record.id,
                            'request_type_id': req_type.id if req_type else False,
                            'stage_id': stage.id if stage else False,
                        })
                        mats_to_add.append(new_mat.id)
                        backup_to_add.append(new_mat.id)

            mats_to_remove = []
            for m in current_mats:
                if m.activity_id and m.activity_id not in selected_activities:
                    mats_to_remove.append(m.id)

            for m in current_mats:
                if m not in backup_mats and m.id not in backup_to_add:
                    backup_to_add.append(m.id)

            cmds = []
            if mats_to_add:
                cmds.extend([(4, mid) for mid in mats_to_add])
            if mats_to_remove:
                cmds.extend([(3, mid) for mid in mats_to_remove])

            write_dict = {}
            if cmds:
                write_dict['material_ids'] = cmds
            if backup_to_add:
                write_dict['material_backup_ids'] = [(4, mid) for mid in backup_to_add]

            if write_dict:
                super(BussmaMarketing, record).write(write_dict)

    def _check_and_move_to_supervisor_approval(self):
        target_stage = self.env.ref('marketing_opportunity_management.stage_mat_marketing_approve', raise_if_not_found=False)
        parent_stage = self.env.ref('marketing_opportunity_management.stage_marketing_supervisor_approval', raise_if_not_found=False)
        if target_stage and parent_stage:
            for record in self:
                rec_seq = record.stage_id.sequence if record.stage_id else 0
                if rec_seq < parent_stage.sequence:
                    if record.material_ids and all(m.stage_id == target_stage or m.material_stage_selection in ['mat_marketing_approve', 'mat_pm_approve', 'mat_done'] for m in record.material_ids):
                        record.write({'stage_id': parent_stage.id})
                        if hasattr(record, '_onchange_stage_id'):
                            record._onchange_stage_id()

    def _send_material_responsible_notification(self):
        template = self.env.ref('marketing_opportunity_management.email_template_marketing_material_responsible_assigned', raise_if_not_found=False)
        for rec in self:
            if rec.material_responsible_id and rec.material_responsible_id.email and template:
                try:
                    email_values = {
                        'email_to': rec.material_responsible_id.email,
                        'email_from': self.env.user.email or self.env.company.email,
                        'model': False,
                        'res_id': False,
                    }
                    template.send_mail(rec.id, force_send=True, email_values=email_values)
                    _logger.info("[Marketing Email] Sent material responsible assignment to %s for marketing ID %s", rec.material_responsible_id.email, rec.id)
                except Exception as e:
                    _logger.error("Failed to send material responsible assignment email for marketing %s: %s", rec.id, str(e))

    def _send_marketing_resent_notification(self):
        template = self.env.ref('marketing_opportunity_management.email_template_marketing_resent_to_marketing', raise_if_not_found=False)
        if not template:
            _logger.warning("[Marketing Email] Template email_template_marketing_resent_to_marketing not found")
            return

        group_supervisor = self.env.ref('marketing_opportunity_management.group_marketing_supervisor', raise_if_not_found=False)

        for rec in self:
            recipient_emails = set()
            if group_supervisor:
                for u in group_supervisor.users.filtered(lambda u: u.active and u.email):
                    recipient_emails.add(u.email.strip())

            if rec.material_responsible_id and rec.material_responsible_id.active and rec.material_responsible_id.email:
                recipient_emails.add(rec.material_responsible_id.email.strip())

            if not recipient_emails:
                _logger.warning("[Marketing Email] No recipient emails found for resent notification on marketing ID %s", rec.id)
                continue

            email_to = ",".join(recipient_emails)
            try:
                email_values = {
                    'email_to': email_to,
                    'email_from': self.env.user.email or self.env.company.email,
                    'model': False,
                    'res_id': False,
                }
                template.send_mail(rec.id, force_send=True, email_values=email_values)
                _logger.info("[Marketing Email] Sent resent notification to %s for marketing ID %s", email_to, rec.id)
            except Exception as e:
                _logger.error("Failed to send marketing resent notification for marketing %s: %s", rec.id, str(e))

    def _send_returned_to_requester_notification(self):
        template = self.env.ref('marketing_opportunity_management.email_template_marketing_returned_to_requester', raise_if_not_found=False)
        if not template:
            _logger.warning("[Marketing Email] Template email_template_marketing_returned_to_requester not found")
            return

        opp_member_emails = self.env['bussma.opportunity.department'].get_opportunity_member_emails()

        for rec in self:
            recipient_emails = set()

            if rec.is_opportunity_request or rec.opportunity_id:
                for email in opp_member_emails:
                    recipient_emails.add(email)

            elif rec.is_office_request or rec.office_request_id:
                off_req = rec.office_request_id
                if off_req and off_req.requested_by_id and off_req.requested_by_id.active and off_req.requested_by_id.email:
                    recipient_emails.add(off_req.requested_by_id.email.strip())
                elif rec.requested_by_id and rec.requested_by_id.active and rec.requested_by_id.email:
                    recipient_emails.add(rec.requested_by_id.email.strip())

            # Fallback
            if not recipient_emails and rec.requested_by_id and rec.requested_by_id.email:
                recipient_emails.add(rec.requested_by_id.email.strip())

            if not recipient_emails:
                _logger.warning("[Marketing Email] No recipient emails found for return notification on marketing ID %s", rec.id)
                continue

            email_to = ",".join(recipient_emails)
            try:
                email_values = {
                    'email_to': email_to,
                    'email_from': self.env.user.email or self.env.company.email,
                    'model': False,
                    'res_id': False,
                }
                template.send_mail(rec.id, force_send=True, email_values=email_values)
                _logger.info("[Marketing Email] Sent return notification to %s for marketing ID %s", email_to, rec.id)
            except Exception as e:
                _logger.error("Failed to send marketing return notification for marketing %s: %s", rec.id, str(e))

    def _send_new_marketing_request_to_supervisor_notification(self):
        template = self.env.ref('marketing_opportunity_management.email_template_new_marketing_request_created', raise_if_not_found=False)
        if not template:
            _logger.warning("[Marketing Email] Template email_template_new_marketing_request_created not found")
            return

        group_supervisor = self.env.ref('marketing_opportunity_management.group_marketing_supervisor', raise_if_not_found=False)
        if not group_supervisor:
            return

        users = group_supervisor.users.filtered(lambda u: u.active and u.email)
        emails = [u.email.strip() for u in users if u.email]
        if not emails:
            _logger.warning("[Marketing Email] No active users with emails found in group_marketing_supervisor for new marketing request")
            return

        email_to = ",".join(set(emails))
        for rec in self:
            try:
                email_values = {
                    'email_to': email_to,
                    'email_from': self.env.user.email or self.env.company.email,
                    'model': False,
                    'res_id': False,
                }
                template.send_mail(rec.id, force_send=True, email_values=email_values)
                _logger.info("[Marketing Email] Sent new marketing request notification to supervisors (%s) for marketing ID %s", email_to, rec.id)
            except Exception as e:
                _logger.error("Failed to send new marketing request notification for marketing %s: %s", rec.id, str(e))

    def _send_property_changed_notification(self, action_type, property_name, is_project=True):
        """
        Send an English email notification to marketing supervisors and responsible users
        when a property is added to or removed from a Project or Opportunity.
        action_type: 'Added' or 'Removed'
        """
        template_xml_id = 'email_template_project_property_changed' if is_project else 'email_template_opportunity_property_changed'
        template = self.env.ref(f'marketing_opportunity_management.{template_xml_id}', raise_if_not_found=False)
        if not template:
            _logger.warning("[Marketing Email] Template %s not found", template_xml_id)
            return

        for rec in self:
            recipients = set()
            group_supervisor = self.env.ref('marketing_opportunity_management.group_marketing_supervisor', raise_if_not_found=False)
            if group_supervisor and group_supervisor.users:
                for u in group_supervisor.users:
                    if u.active and u.email and u.email.strip():
                        recipients.add(u.email.strip())

            if not recipients:
                if rec.user_id and rec.user_id.active and rec.user_id.email:
                    recipients.add(rec.user_id.email.strip())
                if rec.material_responsible_id and rec.material_responsible_id.active and rec.material_responsible_id.email:
                    recipients.add(rec.material_responsible_id.email.strip())

            if not recipients:
                _logger.warning("[Marketing Email] No recipient emails found for property %s notification on marketing %s", action_type, rec.id)
                continue

            email_to = ",".join(recipients)
            ctx = dict(
                self.env.context,
                action_type=action_type,
                property_name=property_name or '',
            )
            try:
                email_values = {
                    'email_to': email_to,
                    'email_from': self.env.user.email or self.env.company.email,
                    'model': False,
                    'res_id': False,
                }
                template.with_context(ctx).send_mail(rec.id, force_send=True, email_values=email_values)
            except Exception as e:
                _logger.error("Failed to send property %s notification for marketing %s: %s", action_type, rec.id, str(e))

    def create_mail_activity(self, users, summary='Request Approval', is_done=True):
        """Create Odoo activities for the specified users on this marketing record."""
        if is_done:
            activities = self.env['mail.activity'].sudo().search([
                ('res_model', '=', self._name),
                ('res_id', 'in', self.ids),
            ])
            if activities:
                activities.action_done()

        if users:
            activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            model_id = self.env['ir.model']._get(self._name).id

            for user in users:
                self.env['mail.activity'].sudo().create({
                    'summary': summary,
                    'activity_type_id': activity_type.id if activity_type else False,
                    'res_model_id': model_id,
                    'res_id': self.id,
                    'user_id': user.id,
                    'date_deadline': fields.Date.today(),
                })

    def _notify_stage_authorized_users(self):
        """Identify authorized users for the current stage and create activities for them."""
        self.ensure_one()
        if not self.stage_id:
            return

        # Always clear old activities when stage changes
        self.create_mail_activity(users=False, is_done=True)

        stage_sel = self.marketing_stage_selection or ''
        if stage_sel == 'mkt_approval':
            users = self.env['res.users']
            group_sup = self.env.ref('marketing_opportunity_management.group_marketing_supervisor', raise_if_not_found=False)
            if group_sup:
                users = group_sup.users.filtered(lambda u: u.active)

            if users:
                summary = _("New marketing request for approval: %s") % (self.name or '')
                self.create_mail_activity(users, summary=summary, is_done=False)
        elif stage_sel == 'mkt_review':
            users = self.env['res.users']
            if self.material_responsible_id and self.material_responsible_id.active:
                users |= self.material_responsible_id
            if users:
                summary = _("Marketing request referred to prepare materials: %s") % (self.name or '')
                self.create_mail_activity(users, summary=summary, is_done=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            source_code = self._get_source_code_from_vals(vals)
            if source_code:
                vals['code'] = source_code
            else:
                if vals.get('code') == '/':
                    vals['code'] = False
        records = super(BussmaMarketing, self).create(vals_list)
        records._sync_materials_from_activities()
        for rec in records:
            if rec.material_responsible_id:
                rec._send_material_responsible_notification()
            rec._notify_stage_authorized_users()
        records._send_new_marketing_request_to_supervisor_notification()
        return records

    def write(self, vals):
        user = self.env.user
        if not self.env.su and not self._context.get('bypass_marketing_check'):
            is_supervisor = user.has_group('marketing_opportunity_management.group_marketing_supervisor')
            for rec in self:
                is_requester = (rec.requested_by_id and rec.requested_by_id == user) or (rec.create_uid and rec.create_uid == user)
                is_proj_mgr = (rec.bussma_project_id and getattr(rec.bussma_project_id, 'project_manager_id', False) == user) or (rec.bussma_project_id and rec.bussma_project_id.create_uid == user)
                is_opp_user = (rec.opportunity_id and (getattr(rec.opportunity_id, 'assigned_user_id', False) == user or rec.opportunity_id.create_uid == user))
                is_office_user = (rec.office_request_id and (getattr(rec.office_request_id, 'requested_by_id', False) == user or rec.office_request_id.create_uid == user))

                if not (is_supervisor or is_requester or is_proj_mgr or is_opp_user or is_office_user):
                    raise UserError(_("Modifying and performing operations on the marketing request is restricted to the marketing supervisor or the requester only."))
        old_responsibles = {rec.id: rec.material_responsible_id for rec in self}
        old_was_returned = {rec.id: rec.is_returned_to_requester for rec in self}
        old_stages = {rec.id: rec.stage_id for rec in self}
        old_stage_sel = {rec.id: rec.marketing_stage_selection for rec in self}
        res = super(BussmaMarketing, self).write(vals)

        if 'marketing_activity_ids' in vals or 'material_ids' in vals:
            self._sync_materials_from_activities()
        if 'material_responsible_id' in vals:
            for rec in self:
                if rec.material_responsible_id and rec.material_responsible_id != old_responsibles.get(rec.id):
                    rec._send_material_responsible_notification()
        if 'is_returned_to_requester' in vals:
            for rec in self:
                if vals['is_returned_to_requester'] is False and old_was_returned.get(rec.id):
                    rec._send_marketing_resent_notification()
                elif vals['is_returned_to_requester'] is True and not old_was_returned.get(rec.id):
                    rec._send_returned_to_requester_notification()

        if 'stage_id' in vals:
            for rec in self:
                if rec.stage_id and rec.stage_id != old_stages.get(rec.id):
                    rec._notify_stage_authorized_users()
                # Cancel marketing_returned activity on opportunity when request is re-sent to marketing
                prev_sel = old_stage_sel.get(rec.id)
                new_sel = rec.marketing_stage_selection
                if prev_sel == 'mkt_draft' and new_sel and new_sel != 'mkt_draft':
                    if rec.opportunity_id:
                        rec.opportunity_id._cancel_opportunity_activities(summary_filter='marketing_returned')

        for rec in self:
            if not rec.code:
                sc = self._get_source_code_from_vals({}, rec=rec)
                if sc:
                    rec.sudo().write({'code': sc})

        return res
