import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class BussmaOpportunity(models.Model):
    _name = 'bussma.opportunity'
    _inherit = 'request'
    _description = 'Opportunity Management'
    _order = 'id desc'
    _rec_names_search = ['name', 'code']

    @api.model
    def _default_stage_id(self):
        req_type = self.env.ref('marketing_opportunity_management.request_type_opportunity', raise_if_not_found=False)
        if req_type:
            return self.env['request.stage'].search([('request_type_ids', 'in', req_type.id)], order='sequence asc', limit=1)
        return self.env['request.stage'].search([('res_model', '=', 'bussma.opportunity')], order='sequence asc', limit=1)

    @api.model
    def _read_group_stage_ids(self, stages, domain=None, order=None):
        req_type = self.env.ref('marketing_opportunity_management.request_type_opportunity', raise_if_not_found=False)
        if req_type:
            return self.env['request.stage'].search([('request_type_ids', 'in', req_type.id)], order='sequence asc')
        return self.env['request.stage'].search([('res_model', '=', 'bussma.opportunity')], order='sequence asc')

    request_type_id = fields.Many2one(
        'request.type',
        string='Request Type',
        default=lambda self: self.env.ref('marketing_opportunity_management.request_type_opportunity', raise_if_not_found=False)
    )
    stage_id = fields.Many2one(
        'request.stage',
        string='Stage',
        default=_default_stage_id,
        group_expand='_read_group_stage_ids',
        domain="[('res_model', '=', 'bussma.opportunity')]",
        tracking=True
    )
    active = fields.Boolean(default=True)
    opportunity_stage_selection = fields.Selection(
        related='stage_id.opportunity_stage_selection',
        string='Stage for Fields',
        store=True
    )
    can_edit_opportunity = fields.Boolean(
        string='Can Edit Opportunity',
        compute='_compute_can_edit_opportunity',
        default=lambda self: self.env.user.has_group('marketing_opportunity_management.group_opportunity_management')
    )
    can_add_attachments = fields.Boolean(
        string='Can Add Attachments',
        compute='_compute_can_add_attachments'
    )
    has_no_entries = fields.Boolean(
        string='Has No Linked Entries',
        compute='_compute_has_no_entries',
        default=True
    )
    is_my_activity = fields.Boolean(
        string="Is My Activity",
        compute="_compute_is_my_activity"
    )
    code = fields.Char(
        string='Opportunity Code',
        readonly=True,
        copy=False,
        default='/'
    )
    name = fields.Char(string='Opportunity Name', required=True, tracking=True)
    opportunity_type = fields.Selection([
        ('commercial_lease', 'Commercial Lease'),
        ('property_sale', 'Property Sale'),
        ('investment', 'Investment'),
        ('development', 'Development')
    ], string='Opportunity Type', required=True, default='property_sale', tracking=True)
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
    ], string='Source', default='system', tracking=True)
    source_other = fields.Char(string='Other Source', tracking=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Priority', default='medium', tracking=True)
    creation_date = fields.Date(
        string='Creation Date',
        default=fields.Date.context_today,
        readonly=True
    )
    expected_closing_date = fields.Date(string='Expected Closing Date', tracking=True)
    assigned_user_id = fields.Many2one(
        'res.users',
        string='Assigned User',
        tracking=True,
        domain=lambda self: [('groups_id', 'in', self.env.ref('marketing_opportunity_management.group_opportunity_contact_officer', raise_if_not_found=False).id)] if self.env.ref('marketing_opportunity_management.group_opportunity_contact_officer', raise_if_not_found=False) else []
    )
    assigned_department = fields.Selection([
        ('commercial', 'Commercial Sector'),
        ('assets_investment', 'Assets and Investment'),
        ('valuation_company', 'Basma Valuation Company  '),
    ], string='Opportunity Type', tracking=True)
    assignment_notes = fields.Text(string='Assignment Notes')
    partner_id = fields.Many2one(
        'res.partner',
        string='Client',
        readonly=False,
        required=True,
        tracking=True
    )
    email = fields.Char(string='Email', readonly=False)
    mobile = fields.Char(
        string='Mobile',
        readonly=False
    )
    city_id = fields.Many2one('res.country.state', string='City', domain="[('country_id.code', '=', 'SA'), ('code', 'ilike', 'CT_')]")
    district_id = fields.Many2one('res.city', string='District', domain="[('state_id', '=', city_id)]")
    client_requirements = fields.Text(string='Client Requirements')
    entry_ids = fields.One2many(
        'entries',
        'opportunity_id',
        string='Entries'
    )
    entries_count = fields.Integer(
        string='Number of Entries',
        compute='_compute_entries_count'
    )
    property_name = fields.Char(string='Property Name')
    property_type_id = fields.Many2one(
        'property.type',
        string='Property Type',
        readonly=False
    )
    area_sqm = fields.Float(
        string='Area (sqm)',
        readonly=False
    )
    location_url = fields.Char(
        string='Location',
        readonly=False
    )
    property_city_id = fields.Many2one(
        'res.country.state',
        string='City',
        domain="[('country_id.code', '=', 'SA'), ('code', 'ilike', 'CT_')]",
        readonly=False
    )
    property_district_id = fields.Many2one(
        'res.city',
        string='District',
        domain="[('state_id', '=', property_city_id)]",
        readonly=False
    )
    approved_pricing = fields.Float(
        string='Approved Pricing',
        compute='_compute_entries_info',
        store=True,
        readonly=False
    )
    committee_decision_rel = fields.Many2one(
        'committee.decision.type',
        string='Committee Decision',
        domain="[('code', 'in', ['direct_sale', 'auction', 'exclusion'])]",
        compute='_compute_entries_info',
        store=True,
        readonly=False
    )
    committee_decision = fields.Char(
        string='Committee Decision Code',
        related='committee_decision_rel.code',
        store=True
    )
    requires_technical_offer = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Requires Technical Offer', compute='_compute_entries_info', store=True, readonly=False)

    marketing_id = fields.Many2one(
        'bussma.marketing',
        string='Marketing',
        tracking=True
    )
    marketing_ids = fields.Many2one(
        'bussma.marketing',
        string='Marketing',
        related='marketing_id',
        readonly=False,
        store=True
    )
    marketing_count = fields.Integer(
        string='Marketing Count',
        compute='_compute_marketing_count'
    )
    marketing_stage_selection = fields.Selection(
        related='marketing_id.marketing_stage_selection',
        string='Marketing Stage',
        readonly=True
    )
    return_to_requester_notes = fields.Text(
        string='Marketing Return Notes',
        tracking=True
    )
    attachment_return_ids = fields.Many2many(
        'ir.attachment',
        'bussma_opportunity_return_attachment_rel',
        'opp_id',
        'attachment_id',
        string='Return Attachments'
    )
    is_returned_to_requester = fields.Boolean(string='Returned to Requester', default=False)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'bussma_opportunity_attachment_rel',
        'opp_id',
        'attachment_id',
        string='Opportunity Attachments'
    )
    material_ids = fields.Many2many(
        'bussma.marketing.material',
        related='marketing_id.material_ids',
        string='Marketing Material Results',
        readonly=True
    )
    material_count = fields.Integer(
        string='Marketing Materials Count',
        compute='_compute_material_count'
    )

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields=allfields, attributes=attributes)
        if res and 'active' in res:
            res['active']['readonly'] = True
            res['active']['invisible'] = True
        return res
    has_pm_or_done_materials = fields.Boolean(
        string='Has PM or Done Materials',
        compute='_compute_has_pm_or_done_materials'
    )
    row_id_notes = fields.Char(string="Row ID")

    @api.depends('marketing_id', 'marketing_id.material_ids', 'marketing_id.material_ids.material_stage_selection')
    def _compute_has_pm_or_done_materials(self):
        for rec in self:
            if rec.marketing_id and rec.marketing_id.material_ids:
                rec.has_pm_or_done_materials = any(
                    m.material_stage_selection in ('mat_pm_approve', 'mat_done')
                    for m in rec.marketing_id.material_ids
                )
            else:
                rec.has_pm_or_done_materials = False

    @api.depends_context('uid')
    @api.depends('activity_ids', 'activity_ids.user_id')
    def _compute_is_my_activity(self):
        current_user = self.env.user
        for record in self:
            record.is_my_activity = any(act.user_id == current_user for act in record.activity_ids)

    @api.depends_context('uid')
    def _compute_can_edit_opportunity(self):
        is_manager = self.env.user.has_group('marketing_opportunity_management.group_opportunity_management')
        for rec in self:
            rec.can_edit_opportunity = is_manager

    @api.depends_context('uid')
    @api.depends('assigned_user_id')
    def _compute_can_add_attachments(self):
        is_manager = self.env.user.has_group('marketing_opportunity_management.group_opportunity_management')
        for rec in self:
            is_officer = bool(rec.assigned_user_id and rec.assigned_user_id == self.env.user)
            rec.can_add_attachments = is_manager or is_officer

    @api.depends('entry_ids')
    def _compute_has_no_entries(self):
        for rec in self:
            rec.has_no_entries = not bool(rec.entry_ids)

    @api.depends('marketing_id', 'marketing_id.material_ids')
    def _compute_material_count(self):
        for rec in self:
            rec.material_count = len(rec.marketing_id.material_ids) if rec.marketing_id else 0

    def action_view_opportunity_materials(self):
        self.ensure_one()
        material_ids = self.marketing_id.material_ids.ids if self.marketing_id else []
        return {
            'name': _('Marketing Materials'),
            'type': 'ir.actions.act_window',
            'res_model': 'bussma.marketing.material',
            'view_mode': 'kanban',
            'domain': [('id', 'in', material_ids)],
            'context': {
                'create': False,
                'edit': False,
                'delete': False,
                'search_default_group_by_stage': 1,
                'hide_new_task': True,
            },
        }

    def _check_opportunity_edit_permission(self):
        if self.env.su or self._context.get('bypass_opportunity_check'):
            return
        if not self.env.user.has_group('marketing_opportunity_management.group_opportunity_management'):
            raise UserError(_("Modifying the opportunity and performing operations is restricted to Opportunity Management only."))

    def _send_assigned_user_notification(self):
        template = self.env.ref('marketing_opportunity_management.email_template_opportunity_user_assigned', raise_if_not_found=False)
        sender_email = self.env.user.email or self.env.company.email
        if not sender_email:
            _logger.warning("[Opportunity Email] Cannot send assignment email: No sender email configured.")
            return
        for rec in self:
            if rec.assigned_user_id and rec.assigned_user_id.email and template:
                try:
                    email_values = {
                        'email_to': rec.assigned_user_id.email,
                        'email_from': sender_email,
                        'model': False,
                        'res_id': False,
                    }
                    template.send_mail(rec.id, force_send=True, email_values=email_values)
                    _logger.info("[Opportunity Email] Sent assignment notification to officer %s", rec.assigned_user_id.email)
                except Exception as e:
                    _logger.error("Failed to send officer assignment email for opportunity %s: %s", rec.id, str(e))

    def _notify_contact_officer_replaced(self, old_user):
        """
        Notify the previous Contact Officer that they have been replaced by another contact officer.
        Sends an email using template email_template_opportunity_user_replaced,
        notifies them via chatter, and clears any open activities for them on this opportunity.
        """
        self.ensure_one()
        if not old_user:
            return

        # 1. Clear old contact officer's activities on this opportunity
        old_activities = self.env['mail.activity'].sudo().search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('user_id', '=', old_user.id),
        ])
        if old_activities:
            old_activities.unlink()

        # 2. Email notification
        if not old_user.email:
            _logger.warning("[Opportunity Email] Old Contact Officer %s has no email address.", old_user.name)
            return

        template = self.env.ref(
            'marketing_opportunity_management.email_template_opportunity_user_replaced',
            raise_if_not_found=False
        )
        if not template:
            _logger.warning("[Opportunity Email] Contact Officer Replaced email template not found.")
            return

        sender_email = self.env.user.email or self.env.company.email
        try:
            email_values = {
                'email_to': old_user.email,
                'email_from': sender_email,
                'model': False,
                'res_id': False,
            }
            template.with_context(
                old_user_name=old_user.name,
                old_user_email=old_user.email
            ).send_mail(self.id, force_send=True, email_values=email_values)
            _logger.info("[Opportunity Email] Sent replacement notification to previous officer %s", old_user.email)
        except Exception as e:
            _logger.error("Failed to send officer replacement email for opportunity %s: %s", self.id, str(e))

    def _clean_chatter_attachment_links(self):
        for rec in self:
            if rec.attachment_ids:
                atts_to_fix = rec.attachment_ids.sudo().filtered(lambda a: a.res_model == 'bussma.opportunity')
                if atts_to_fix:
                    atts_to_fix.write({
                        'res_model': 'bussma.opportunity.attachment',
                        'res_id': 0,
                    })

    # ─────────────────────────────────────────────
    # Opportunity Activity Notifications
    # ─────────────────────────────────────────────
    def _create_opportunity_activity(self, summary, note):
        """
        Create a mail.activity on this opportunity for every user in
        group_opportunity_management. Existing activities with the same
        summary are removed first to avoid duplicates.
        """
        for rec in self:
            if not rec.id or not isinstance(rec.id, int):
                continue
            target_users = rec.env['bussma.opportunity.department'].get_opportunity_members()
            if not target_users:
                continue

            # Remove existing activities with same summary on this record
            rec._cancel_opportunity_activities(summary_filter=summary)

            activity_type = rec.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            model_id = rec.env['ir.model']._get(rec._name).id
            for user in target_users:
                try:
                    rec.env['mail.activity'].sudo().with_context(
                        mail_activity_quick_update=True,
                        mail_create_nosubscribe=True,
                    ).create({
                        'summary': summary,
                        'note': note,
                        'activity_type_id': activity_type.id if activity_type else False,
                        'res_model_id': model_id,
                        'res_id': rec.id,
                        'user_id': user.id,
                        'date_deadline': fields.Date.today(),
                    })
                except Exception as e:
                    _logger.error(
                        "[Opportunity Activity] Failed to create activity for user %s on opp %s: %s",
                        user.id, rec.id, str(e)
                    )

    def _cancel_opportunity_activities(self, summary_filter=None):
        """
        Cancel/unlink pending mail.activity records on this opportunity.
        If summary_filter is provided, only activities whose summary
        starts with summary_filter are cancelled.
        """
        for rec in self:
            if not rec.id or not isinstance(rec.id, int):
                continue
            domain = [
                ('res_model', '=', 'bussma.opportunity'),
                ('res_id', '=', rec.id),
            ]
            activities = rec.env['mail.activity'].sudo().search(domain)
            if summary_filter:
                activities = activities.filtered(
                    lambda a: a.summary and a.summary.startswith(summary_filter)
                )
            if activities:
                activities.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and not self._context.get('bypass_opportunity_check'):
            if not self.env.user.has_group('marketing_opportunity_management.group_opportunity_management'):
                raise UserError(_("Creating opportunities directly is restricted to members of the Opportunity Management group."))
        req_type = self.env.ref('marketing_opportunity_management.request_type_opportunity', raise_if_not_found=False)
        for vals in vals_list:
            if vals.get('code', '/') == '/':
                vals['code'] = self.env['ir.sequence'].next_by_code('bussma.opportunity') or '/'
            if req_type and not vals.get('request_type_id'):
                vals['request_type_id'] = req_type.id
        records = super(BussmaOpportunity, self).create(vals_list)
        records._clean_chatter_attachment_links()
        records._sync_entry_attachments()
        for rec in records:
            if rec.assigned_user_id:
                rec._send_assigned_user_notification()
        return records

    def write(self, vals):
        if not self.env.su and not self._context.get('bypass_opportunity_check') and not self._context.get('bypass_attachment_check'):
            has_opp_mgr = self.env.user.has_group('marketing_opportunity_management.group_opportunity_management')
            has_mkt_sup = self.env.user.has_group('marketing_opportunity_management.group_marketing_supervisor')
            if not (has_opp_mgr or has_mkt_sup):
                for field_name in ('attachment_ids', 'attachment_return_ids'):
                    if field_name in vals and vals[field_name]:
                        for rec in self:
                            existing_ids = set(rec[field_name].ids)
                            for cmd in vals[field_name]:
                                if not isinstance(cmd, (tuple, list)) or not cmd:
                                    continue
                                cmd_type = cmd[0]
                                if cmd_type in (2, 3, 5):
                                    raise UserError(_("Deleting or removing attachments from this opportunity is restricted to Opportunity Management"))
                                elif cmd_type == 6:
                                    new_ids = set(cmd[2]) if len(cmd) > 2 and cmd[2] else set()
                                    if not existing_ids.issubset(new_ids):
                                        raise UserError(_("Deleting or removing attac hments from this opportunity is restricted to Opportunity Management"))

        # Check restriction on modifying name and assigned_user_id in opp_approve_close or opp_contracted
        if not self.env.su and not self._context.get('bypass_opportunity_check'):
            if 'stage_id' in vals:
                target_stage = self.env['request.stage'].browse(vals['stage_id'])
                if target_stage.opportunity_stage_selection == 'opp_approve_close':
                    for rec in self:
                        rec._validate_opportunity_closure()
            for rec in self:
                if rec.opportunity_stage_selection in ('opp_approve_close', 'opp_contracted'):
                    if 'name' in vals and vals['name'] != rec.name:
                        raise UserError(_("Modifying opportunity name is not allowed in '%s' stage.") % rec.stage_id.name)
                    if 'assigned_user_id' in vals and vals['assigned_user_id'] != rec.assigned_user_id.id:
                        raise UserError(_("Modifying contact officer is not allowed in '%s' stage.") % rec.stage_id.name)

        old_assigned = {rec.id: rec.assigned_user_id for rec in self}
        old_entries = {rec.id: set(rec.entry_ids.ids) for rec in self}
        old_stage_sel = {rec.id: rec.opportunity_stage_selection for rec in self}
        ctx_self = self.with_context(bypass_entry_notify=True) if 'entry_ids' in vals else self
        res = super(BussmaOpportunity, ctx_self).write(vals)
        if 'attachment_ids' in vals:
            self._clean_chatter_attachment_links()
        if 'entry_ids' in vals:
            self.with_context(bypass_opportunity_check=True)._sync_entry_attachments()
            for rec in self:
                old_set = old_entries.get(rec.id, set())
                new_set = set(rec.entry_ids.ids)
                added_ids = new_set - old_set
                removed_ids = old_set - new_set

                if added_ids:
                    added_entries = self.env['entries'].browse(list(added_ids))
                    added_names = ", ".join(filter(None, added_entries.mapped(lambda e: e.entrie_name or f"Listing #{e.id}")))
                    rec.message_post(body=_("Property (%s) was added to opportunity properties.") % added_names)
                    if rec.marketing_id:
                        rec.marketing_id._send_property_changed_notification(action_type=_('Added'), property_name=added_names, is_project=False)

                if removed_ids:
                    removed_entries = self.env['entries'].browse(list(removed_ids))
                    removed_names = ", ".join(filter(None, removed_entries.mapped(lambda e: e.entrie_name or f"Listing #{e.id}")))
                    rec.message_post(body=_("Property (%s) was removed from opportunity properties.") % removed_names)
                    if rec.marketing_id:
                        rec.marketing_id._send_property_changed_notification(action_type=_('Removed'), property_name=removed_names, is_project=False)

                if rec.marketing_id:
                    rec.marketing_id.sudo().with_context(bypass_marketing_check=True).write({
                        'entry_ids': [(6, 0, rec.entry_ids.ids)]
                    })
        if 'assigned_user_id' in vals:
            for rec in self:
                old_user = old_assigned.get(rec.id)
                new_user = rec.assigned_user_id
                if old_user and new_user and old_user != new_user:
                    rec._notify_contact_officer_replaced(old_user)
                    rec._send_assigned_user_notification()
                elif not old_user and new_user:
                    rec._send_assigned_user_notification()
        # Cancel final_material activity and send email to contact officer when opportunity moves to opp_approve_close
        if 'stage_id' in vals:
            for rec in self:
                prev_sel = old_stage_sel.get(rec.id)
                new_sel = rec.opportunity_stage_selection
                if new_sel == 'opp_approve_close' and prev_sel != 'opp_approve_close':
                    rec._cancel_opportunity_activities(summary_filter='final_material')
                    rec._send_opportunity_mail_template('marketing_opportunity_management.email_template_opportunity_approve_close')
        return res

    @api.depends('name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name

    @api.depends('entry_ids')
    def _compute_entries_count(self):
        for rec in self:
            rec.entries_count = len(rec.entry_ids)

    @api.onchange('entry_ids')
    def _onchange_entry_ids(self):
        if self.entry_ids:
            first = self.entry_ids[0]
            is_first_assignment = (len(self.entry_ids) == 1) or (not self.area_sqm and not self.location_url)
            if is_first_assignment:
                if first.property_type and not self.property_type_id:
                    self.property_type_id = first.property_type.id
                if first.area_sqm and not self.area_sqm:
                    self.area_sqm = first.area_sqm
                if first.city and not self.property_city_id:
                    self.property_city_id = first.city.id
                if first.district_id and not self.property_district_id:
                    self.property_district_id = first.district_id.id
                if first.location_url and not self.location_url:
                    self.location_url = first.location_url
                if first.partner_id and not self.partner_id:
                    self.partner_id = first.partner_id.id
                mobile_val = first.partner_mobile or (first.partner_id.mobile if first.partner_id else False)
                if mobile_val and not self.mobile:
                    self.mobile = mobile_val

    @api.depends(
        'entry_ids',
        'entry_ids.committee_total_price',
        'entry_ids.committee_decision_rel',
        'entry_ids.committee_decision',
        'entry_ids.requires_technical_offer',
        'entry_ids.stage_id',
        'entry_ids.stage_id.project_stage_selection'
    )
    def _compute_entries_info(self):
        for rec in self:
            if rec.entry_ids:
                # Filter entries that have moved past committee decision or reached completed stages
                eligible_entries = rec.entry_ids.filtered(lambda e: e.stage_id.project_stage_selection in [
                    'sales_manager_decision', 'auctions_manager_decision',
                    'commercial_manager_approval', 'assign_negotiator',
                    'negotiator', 'manager_contract_approval', 'contract_followup',
                    'contract_completion', 'completed', 'city_study_completed'
                ])
                target_entries = eligible_entries if eligible_entries else rec.entry_ids
                target_first = target_entries[0]

                rec.approved_pricing = sum(e.committee_total_price for e in target_entries)
                if hasattr(target_first, 'committee_decision_rel') and target_first.committee_decision_rel:
                    rec.committee_decision_rel = target_first.committee_decision_rel.id
                elif target_first.committee_decision:
                    cd = self.env['committee.decision.type'].search([('code', '=', target_first.committee_decision)], limit=1)
                    rec.committee_decision_rel = cd.id if cd else False
                else:
                    rec.committee_decision_rel = False

                rec.requires_technical_offer = target_first.requires_technical_offer or False
            else:
                rec.approved_pricing = 0.0
                rec.committee_decision_rel = False
                rec.requires_technical_offer = False

            if rec.id and isinstance(rec.id, int):
                rec._sync_entry_attachments()

    def _update_study_data_from_entries(self):
        for rec in self:
            if not rec.id or not isinstance(rec.id, int):
                continue
            rec._compute_entries_info()
            rec._compute_entries_count()
            if rec.entry_ids:
                first = rec.entry_ids[0]
                vals = {}
                is_first_assignment = (len(rec.entry_ids) == 1) or (not rec.area_sqm and not rec.location_url)
                if is_first_assignment:
                    if first.property_type and not rec.property_type_id:
                        vals['property_type_id'] = first.property_type.id
                    if first.area_sqm and not rec.area_sqm:
                        vals['area_sqm'] = first.area_sqm
                    if first.location_url and not rec.location_url:
                        vals['location_url'] = first.location_url
                    if first.city and not rec.property_city_id:
                        vals['property_city_id'] = first.city.id
                    if first.district_id and not rec.property_district_id:
                        vals['property_district_id'] = first.district_id.id
                    if first.partner_id and not rec.partner_id:
                        vals['partner_id'] = first.partner_id.id
                    mobile_val = first.partner_mobile or (first.partner_id.mobile if first.partner_id else False)
                    if mobile_val and not rec.mobile:
                        vals['mobile'] = mobile_val
                if vals:
                    rec.sudo().write(vals)

    def _send_opportunity_mail_template(self, template_xmlid, extra_context=None):
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if not template:
            _logger.warning("[Opportunity Mail Template] Template '%s' was not found.", template_xmlid)
            return

        ctx = dict(self.env.context)
        if extra_context:
            ctx.update(extra_context)
        if 'action_user_name' not in ctx or not ctx['action_user_name']:
            ctx['action_user_name'] = self.env.user.name or ''

        dept_member_emails = self.env['bussma.opportunity.department'].get_opportunity_member_emails()

        # Contact Officer receives email notification for final_material_sent and approve_close templates
        should_include_assigned_user = (template_xmlid in [
            'marketing_opportunity_management.email_template_opportunity_final_material_sent',
            'marketing_opportunity_management.email_template_opportunity_approve_close',
        ])

        for rec in self:
            recipient_emails = set(dept_member_emails)

            if should_include_assigned_user and rec.assigned_user_id and rec.assigned_user_id.active and rec.assigned_user_id.email:
                recipient_emails.add(rec.assigned_user_id.email.strip())

            if not recipient_emails:
                _logger.warning(
                    "[Opportunity Mail Template %s] No recipient email found for Opp ID %s (%s). "
                    "Please assign a Contact Officer with an email or add members with email to Opportunity Department.",
                    template_xmlid, rec.id, rec.name
                )
                continue

            email_to = ",".join(recipient_emails)
            try:
                email_values = {
                    'email_to': email_to,
                    'email_from': self.env.user.email or self.env.company.email,
                    'model': False,
                    'res_id': False,
                }
                template.with_context(ctx).send_mail(rec.id, force_send=True, email_values=email_values)
                _logger.info("[Opportunity Mail Template %s] Sent to %s for Opp ID %s", template_xmlid, email_to, rec.id)
            except Exception as e:
                _logger.error("[Opportunity Mail Template Error %s] Opp %s: %s", template_xmlid, rec.id, str(e))

    def _send_new_property_added_to_marketing_notification(self, property_names=None):
        template = self.env.ref('marketing_opportunity_management.email_template_opportunity_new_property_added_to_marketing', raise_if_not_found=False)
        group_supervisor = self.env.ref('marketing_opportunity_management.group_marketing_supervisor', raise_if_not_found=False)
        if not template or not group_supervisor:
            return

        users = group_supervisor.users.filtered(lambda u: u.active and u.email)
        emails = [u.email.strip() for u in users if u.email]
        if not emails:
            return

        email_to = ",".join(set(emails))
        for rec in self:
            if not rec.marketing_id:
                continue
            entry_names = property_names or ", ".join(filter(None, rec.entry_ids.mapped(lambda e: e.entrie_name or f"Listing #{e.id}")))
            ctx = dict(
                self.env.context,
                added_property_name=entry_names,
                action_user_name=self.env.user.name or ''
            )
            try:
                email_values = {
                    'email_to': email_to,
                    'email_from': self.env.user.email or self.env.company.email,
                    'model': False,
                    'res_id': False,
                }
                template.with_context(ctx).send_mail(rec.id, force_send=True, email_values=email_values)
                _logger.info("[Opportunity New Property Notification] Sent to supervisors %s for Opp ID %s", email_to, rec.id)
            except Exception as e:
                _logger.error("Failed to send new property notification for Opp %s: %s", rec.id, str(e))

    def _sync_entry_attachments(self):
        for rec in self.sudo():
            if not rec.id or not isinstance(rec.id, int) or not rec.entry_ids:
                continue
            entry_attachments = self.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'entries'),
                ('res_id', 'in', rec.entry_ids.ids)
            ])
            m2m_attachments = (
                rec.entry_ids.sudo().mapped('facility_photo_ids') |
                rec.entry_ids.sudo().mapped('rent_contract_ids') |
                rec.entry_ids.sudo().mapped('direct_sale_contract_attachments') |
                rec.entry_ids.sudo().mapped('auction_contract_attachments')
            )
            all_attachments = entry_attachments | m2m_attachments
            if not all_attachments:
                continue

            # 1. Sync to Opportunity (bussma.opportunity)
            existing_opp_attachments = rec.attachment_ids
            existing_opp_keys = set()
            for opp_att in existing_opp_attachments:
                if opp_att.checksum:
                    existing_opp_keys.add(('checksum', opp_att.checksum))
                if opp_att.name:
                    existing_opp_keys.add(('name', opp_att.name))

            copied_to_opp = False
            for att in all_attachments:
                key_checksum = ('checksum', att.checksum) if att.checksum else None
                key_name = ('name', att.name) if att.name else None
                if (key_checksum and key_checksum in existing_opp_keys) or (key_name and key_name in existing_opp_keys):
                    continue
                copied_att = att.sudo().copy({
                    'res_model': 'bussma.opportunity.attachment',
                    'res_id': 0,
                })
                rec.write({'attachment_ids': [(4, copied_att.id)]})
                copied_to_opp = True
                if key_checksum:
                    existing_opp_keys.add(key_checksum)
                if key_name:
                    existing_opp_keys.add(key_name)

            # 2. Sync to Marketing Request (bussma.marketing) if linked
            if rec.marketing_id:
                existing_mkt_attachments = self.env['ir.attachment'].search([
                    ('res_model', '=', 'bussma.marketing'),
                    ('res_id', '=', rec.marketing_id.id)
                ])
                existing_mkt_keys = set()
                for mkt_att in existing_mkt_attachments:
                    if mkt_att.checksum:
                        existing_mkt_keys.add(('checksum', mkt_att.checksum))
                    if mkt_att.name:
                        existing_mkt_keys.add(('name', mkt_att.name))

                for att in all_attachments:
                    key_checksum = ('checksum', att.checksum) if att.checksum else None
                    key_name = ('name', att.name) if att.name else None
                    if (key_checksum and key_checksum in existing_mkt_keys) or (key_name and key_name in existing_mkt_keys):
                        continue
                    att.copy({
                        'res_model': 'bussma.marketing',
                        'res_id': rec.marketing_id.id,
                    })
                    if key_checksum:
                        existing_mkt_keys.add(key_checksum)
                    if key_name:
                        existing_mkt_keys.add(key_name)

            if copied_to_opp:
                entry_names = ", ".join(filter(None, rec.entry_ids.mapped(lambda e: e.entrie_name or f"Listing #{e.id}")))
                rec._send_opportunity_mail_template(
                    'marketing_opportunity_management.email_template_opportunity_attachments_updated',
                    extra_context={
                        'entry_name': entry_names,
                        'action_user_name': self.env.user.name or ''
                    }
                )

    def action_open_marketing_request_wizard(self):
        self.ensure_one()
        self._check_opportunity_edit_permission()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Marketing Request'),
            'res_model': 'bussma.marketing.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_opportunity_id': self.id,
                'default_marketing_id': self.marketing_id.id if self.marketing_id else False,
                'default_opportunity_name': self.name,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
                'default_property_name': self.property_name or '',
                'default_property_type_id': self.property_type_id.id if self.property_type_id else False,
                'default_city_id': self.property_city_id.id if self.property_city_id else False,
                'default_district_id': self.property_district_id.id if self.property_district_id else False,
                'default_area_sqm': self.area_sqm,
                'default_sale_price': self.approved_pricing,
                'default_opportunity_type': self.opportunity_type,
                'default_source': self.source,
                'default_opportunity_source': self.opportunity_source,
                'default_source_other': self.source_other,
                'default_priority': self.priority,
                'default_client_requirements': self.client_requirements or '',
                'default_name': f"{self.name}",
                'default_attachments_ids': self.attachment_ids.ids,
                'default_entry_ids': [(6, 0, self.entry_ids.ids)],
            }
        }

    def action_open_assign_wizard(self):
        self.ensure_one()
        self._check_opportunity_edit_permission()
        if not self.partner_id:
            raise UserError(_("Please select the client first."))
        assign_list_view = self.env.ref(
            'marketing_opportunity_management.view_entries_assign_opportunity_list',
            raise_if_not_found=False,
        )
        domain = [
            ('partner_id', '=', self.partner_id.id),
            ('stage_id.project_stage_selection', '!=', 'completed'),
            ('opportunity_id', '=', False),
        ]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Select Properties to Assign to Opportunity'),
            'res_model': 'entries',
            'view_mode': 'list',
            'views': [(assign_list_view.id if assign_list_view else False, 'list')],
            'domain': domain,
            'context': {
                'opportunity_to_assign': self.id,
            },
            'target': 'new',
        }

    def action_open_assign_entries_wizard(self):
        return self.action_open_assign_wizard()

    def action_move_to_data_completion(self):
        self.ensure_one()
        self._check_opportunity_edit_permission()
        stage = self.env.ref('marketing_opportunity_management.stage_opportunity_data_completion', raise_if_not_found=False)
        if stage:
            self.write({'stage_id': stage.id})

    def action_move_to_marketing_request(self):
        self.ensure_one()
        self._check_opportunity_edit_permission()
        stage = self.env.ref('marketing_opportunity_management.stage_opportunity_marketing_request', raise_if_not_found=False)
        if stage:
            self.write({'stage_id': stage.id})

    def action_move_to_final_material(self):
        self.ensure_one()
        self._check_opportunity_edit_permission()
        stage = self.env.ref('marketing_opportunity_management.stage_opportunity_final_material', raise_if_not_found=False)
        if stage:
            self.write({'stage_id': stage.id})

    def _validate_opportunity_closure(self):
        self.ensure_one()
        errors = []

        mkt_records = self.marketing_id | self.env['bussma.marketing'].search([('opportunity_id', '=', self.id)])
        materials = self.material_ids | mkt_records.mapped('material_ids') | self.env['bussma.marketing.material'].search([('marketing_id', 'in', mkt_records.ids)])
        pending_materials = materials.filtered(lambda m: m.material_stage_selection != 'mat_done')
        if pending_materials:
            names = ", ".join(pending_materials.mapped(lambda m: m.name or str(m.id)))
            errors.append(_("Marketing Materials: %s") % names)

        if errors:
            raise UserError(
                _("Cannot close opportunity because the following materials are not completed:\n\n%s")
                % "\n\n".join(errors)
            )

    def action_move_to_approve_close(self):
        self.ensure_one()
        self._check_opportunity_edit_permission()
        self._validate_opportunity_closure()
        stage = self.env.ref('marketing_opportunity_management.stage_opportunity_approve_close', raise_if_not_found=False)
        if stage:
            self.write({'stage_id': stage.id})

    def action_move_to_contracted(self):
        self.ensure_one()
        self._check_opportunity_edit_permission()
        stage = self.env.ref('marketing_opportunity_management.stage_opportunity_contracted', raise_if_not_found=False)
        if stage:
            self.write({'stage_id': stage.id})

    def action_return_to_final_material(self):
        self.ensure_one()
        self._check_opportunity_edit_permission()
        stage = self.env.ref('marketing_opportunity_management.stage_opportunity_final_material', raise_if_not_found=False)
        if stage:
            self.write({'stage_id': stage.id})
