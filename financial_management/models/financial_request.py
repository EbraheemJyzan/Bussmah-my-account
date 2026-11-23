import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class FinancialRequest(models.Model):
    _name = 'financial.request'
    _description = 'Financial Management - Invoice Request'
    _inherit = 'request'
    _order = 'id desc'
    _rec_names_search = ['project_name', 'code']

    @api.model
    def web_search_read(self, domain=None, specification=None, offset=0, limit=None, order=None, count_limit=None):
        user = self.env.user
        domain = domain or []
        is_manager = (
            user.has_group('base.group_system') or
            user.has_group('financial_management.group_financial_management') or
            user.has_group('financial_management.group_financial_management_accountant') or
            user.has_group('marketing_opportunity_management.group_marketing_supervisor') or
            user.has_group('sales_and_auction_management.group_commercial_sector_accountant') or
            user.has_group('bussma_system.group_commercial_sector_manager') or
            user.has_group('bussma_system.group_sales_manager') or
            user.has_group('bussma_system.group_auctions_manager')
        )
        if not is_manager:
            my_domain = ['|', ('create_uid', '=', user.id), ('requester_id', '=', user.id)]
            domain = expression.AND([domain, my_domain])

        return super().web_search_read(
            domain=domain,
            specification=specification,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit
        )

    # ─────────────────────────────────────────────
    # Stage helpers (same pattern as bussma.marketing)
    # ─────────────────────────────────────────────
    def _default_stage_id(self):
        req_type = self.env.ref(
            'financial_management.request_type_financial',
            raise_if_not_found=False
        )
        if req_type:
            return self.env['request.stage'].search(
                [('request_type_ids', 'in', req_type.id)],
                order='sequence asc', limit=1
            )
        return False

    @api.model
    def _read_group_stage_ids(self, stages, domain=None, order=None):
        req_type = self.env.ref(
            'financial_management.request_type_financial',
            raise_if_not_found=False
        )
        if req_type:
            return self.env['request.stage'].search(
                [('request_type_ids', 'in', req_type.id)],
                order='sequence asc'
            )
        return self.env['request.stage'].search(
            [('res_model', '=', 'financial.request')],
            order='sequence asc'
        )

    # ─────────────────────────────────────────────
    # Request type & Stage
    # ─────────────────────────────────────────────
    request_type_id = fields.Many2one(
        'request.type',
        string='Request Type (System)',
        default=lambda self: self.env.ref(
            'financial_management.request_type_financial',
            raise_if_not_found=False
        )
    )
    active = fields.Boolean(default=True)
    stage_id = fields.Many2one(
        'request.stage',
        string='Stage',
        default=_default_stage_id,
        group_expand='_read_group_stage_ids',
        domain="[('res_model', '=', 'financial.request')]",
        tracking=True
    )
    financial_stage_selection = fields.Selection(
        related='stage_id.financial_stage_selection',
        string='Stage Selection',
        store=True
    )
    code = fields.Char(
        string='Request Number',
        required=True,
        readonly=True,
        copy=False,
        default='/'
    )
    requester_id = fields.Many2one(
        'res.users',
        string='Requester Name',
        default=lambda self: self.env.user,
        tracking=True
    )
    department = fields.Selection([
        ('direct_sales', 'Direct Sales'),
        ('auctions', 'Auctions'),
        ('marketing', 'Marketing'),
    ], string='Department', required=True, tracking=True)
    project_name = fields.Char(
        string='Project Name',
        tracking=True
    )
    marketing_material_id = fields.Many2one(
        'bussma.marketing.material',
        string='Marketing Material',
        tracking=True,
        domain="[('marketing_id', '=', marketing_id)]"
    )
    marketing_id = fields.Many2one(
        'bussma.marketing',
        string='Marketing Project',
        tracking=True
    )
    marketing_id_domain = fields.Char(
        string='Marketing ID Domain',
        compute='_compute_marketing_id_domain',
    )
    invoice_type = fields.Selection([
        ('cost', 'Cost Invoices'),
        ('supplier', 'Supplier Invoices'),
    ], string='Invoice Type', tracking=True)
    invoice_amount = fields.Monetary(
        string='Invoice Amount (SAR)',
        currency_field='currency_id',
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    invoice_description = fields.Text(
        string='Invoice Description',
        tracking=True
    )
    supplier_name = fields.Char(
        string='Supplier Name',
        tracking=True
    )
    request_type = fields.Selection([
        ('sofa_hall_rent', 'Hall Sofa Rental'),
        ('hall_booking_fees', 'Hall Reservation Fees'),
        ('decorations_entertainment', 'Decorations & Entertainment'),
        ('auction_tools', 'Auction Tools'),
        ('hospitality_distributions', 'Hospitality & Giveaways'),
        ('real_estate_photography', 'Real Estate Photography'),
        ('shield_box', 'Shield Box'),
        ('shield_box_contents', 'Shield Box Contents'),
        ('brochure_printing', 'Brochures Printing'),
        ('digital_apps_accounts', 'Digital Applications & Ad Accounts'),
        ('audio_recording', 'Audio Recording'),
        ('influencer_campaigns', 'Influencer Campaigns'),
        ('tv_advertisement', 'TV Advertisement'),
        ('radio', 'Radio'),
        ('advertising_campaign_costs', 'Ad Campaign Costs'),
        ('road_billboards', 'Roadside Billboards'),
        ('emcee_costs', 'Auctioneer Costs'),
        ('billboard_installation_costs', 'Billboard Installation Costs'),
        ('removal_costs', 'Removal Operation Costs'),
        ('other', 'Other'),
    ], string='Request Type', required=True, tracking=True)
    includes_vat = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Does the Invoice Amount Include VAT?', tracking=True)
    iban_attachment_ids = fields.Many2many(
        'ir.attachment',
        'financial_request_iban_att_rel',
        'request_id',
        'attachment_id',
        string='Supplier Bank IBAN Attachments'
    )
    tax_invoice_attachment_ids = fields.Many2many(
        'ir.attachment',
        'financial_request_tax_inv_att_rel',
        'request_id',
        'attachment_id',
        string='Tax Invoice Attachments'
    )
    notes = fields.Text(
        string='Notes',
        tracking=True
    )
    marketing_mgr_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Marketing Manager Approval', tracking=True)
    marketing_mgr_notes = fields.Text(string='Marketing Manager Notes', tracking=True)
    sector_accountant_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Commercial Sector Accountant Approval', tracking=True)
    sector_accountant_notes = fields.Text(string='Commercial Sector Accountant Notes', tracking=True)
    dept_mgr_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Department Manager Approval', tracking=True)
    dept_mgr_notes = fields.Text(string='Department Manager Notes', tracking=True)
    sector_mgr_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Commercial Sector Manager Approval', tracking=True)
    sector_mgr_notes = fields.Text(string='Commercial Sector Manager Notes', tracking=True)
    admin_accountant_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Administration Accountant Approval', tracking=True)
    admin_accountant_notes = fields.Text(string='Administration Accountant Notes', tracking=True)
    financial_mgr_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Financial Management Manager Approval', tracking=True)
    financial_mgr_notes = fields.Text(string='Financial Management Manager Notes', tracking=True)
    is_returned = fields.Boolean(string='Request Returned', default=False, tracking=True)
    return_notes = fields.Text(string='Return Notes', tracking=True)
    receipts_count = fields.Integer(
        string='Receipts Count',
        tracking=True
    )
    receipt_attachment_ids = fields.Many2many(
        'ir.attachment',
        'financial_request_receipt_att_rel',
        'request_id',
        'attachment_id',
        string='Attach Receipts'
    )
    date = fields.Date(string="Request date", default=fields.Date.today, tracking=True)
    is_cancelled = fields.Boolean(
        string='Cancelled Request',
        default=False,
        tracking=True,
        help='Indicates if this request is cancelled'
    )
    is_rejected = fields.Boolean(
        string='Rejected Request',
        default=False,
        tracking=True,
        help='Indicates if this request is rejected'
    )
    # ─────────────────────────────────────────────
    # Computed Stage Permission Check Fields
    # ─────────────────────────────────────────────
    can_submit_draft = fields.Boolean(compute='_compute_stage_permissions')
    can_approve_marketing_mgr = fields.Boolean(compute='_compute_stage_permissions')
    can_approve_sector_accountant = fields.Boolean(compute='_compute_stage_permissions')
    can_approve_dept_mgr = fields.Boolean(compute='_compute_stage_permissions')
    can_approve_sector_mgr = fields.Boolean(compute='_compute_stage_permissions')
    can_approve_admin_accountant = fields.Boolean(compute='_compute_stage_permissions')
    can_approve_financial_mgr = fields.Boolean(compute='_compute_stage_permissions')
    can_attach_receipts = fields.Boolean(compute='_compute_stage_permissions')
    row_id_notes = fields.Char(string='Row ID')

    def action_toggle_cancelled(self):
        user = self.env.user
        if not (user.has_group('base.group_system') or user.has_group('financial_management.group_financial_management')):
            raise UserError(_("You do not have permission to change the cancelled status."))
        for rec in self:
            if not rec.is_cancelled:
                rec.is_cancelled = True
            else:
                rec.is_cancelled = False

    def action_toggle_rejected(self):
        user = self.env.user
        if not (user.has_group('base.group_system') or user.has_group('financial_management.group_financial_management')):
            raise UserError(_("You do not have permission to change the rejected status."))
        for rec in self:
            if not rec.is_rejected:
                rec.is_rejected = True
            else:
                rec.is_rejected = False

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields=allfields, attributes=attributes)
        if res and 'active' in res:
            res['active']['readonly'] = True
            res['active']['invisible'] = True
        return res

    @api.depends_context('uid')
    @api.depends('marketing_id', 'marketing_material_id', 'department', 'request_type', 'financial_stage_selection')
    def _compute_stage_permissions(self):
        user = self.env.user
        is_fin_manager = user.has_group('financial_management.group_financial_management')
        for rec in self:
            rec.can_submit_draft = bool(is_fin_manager)
            rec.can_approve_marketing_mgr = user in rec._get_stage_target_users('fin_marketing_mgr')
            rec.can_approve_sector_accountant = user in rec._get_stage_target_users('fin_sector_accountant')
            rec.can_approve_dept_mgr = user in rec._get_stage_target_users('fin_dept_mgr')
            rec.can_approve_sector_mgr = user in rec._get_stage_target_users('fin_sector_mgr')
            rec.can_approve_admin_accountant = user in rec._get_stage_target_users('fin_admin_accountant')
            rec.can_approve_financial_mgr = user in rec._get_stage_target_users('fin_financial_mgr')
            rec.can_attach_receipts = user in rec._get_stage_target_users('fin_attach_receipts')

    @api.depends('code', 'project_name')
    def _compute_display_name(self):
        for rec in self:
            if rec.project_name:
                rec.display_name = f"[{rec.code}] {rec.project_name}"
            else:
                rec.display_name = rec.code or '/'

    @api.onchange('marketing_id')
    def _onchange_marketing_id(self):
        if self.marketing_id:
            self.project_name = self.marketing_id.name
            if self.marketing_material_id and self.marketing_material_id.marketing_id != self.marketing_id:
                self.marketing_material_id = False

    @api.depends('department')
    def _compute_marketing_id_domain(self):
        for rec in self:
            if rec.department == 'marketing':
                rec.marketing_id_domain = str(
                    [('project_status', '!=', 'done')]
                )
            elif rec.department == 'direct_sales':
                rec.marketing_id_domain = str([
                    '|',
                    ('bussma_project_id.project_type', '=', 'sales'),
                    ('project_type_selection', '=', 'sales'),
                ])
            elif rec.department == 'auctions':
                rec.marketing_id_domain = str([
                    '|',
                    ('bussma_project_id.project_type', 'in', ['auction_pvt', 'auction_enf', 'city']),
                    ('project_type_selection', 'in', ['auction_pvt', 'auction_enf', 'city']),
                ])
            else:
                rec.marketing_id_domain = str([])

    @api.onchange('department')
    def _onchange_department(self):
        if self.marketing_id and self.department:
            domain = []
            if self.department == 'marketing':
                domain = [('project_status', '!=', 'done')]
            elif self.department == 'direct_sales':
                domain = [
                    '|',
                    ('bussma_project_id.project_type', '=', 'sales'),
                    ('project_type_selection', '=', 'sales'),
                ]
            elif self.department == 'auctions':
                domain = [
                    '|',
                    ('bussma_project_id.project_type', 'in', ['auction_pvt', 'auction_enf', 'city']),
                    ('project_type_selection', 'in', ['auction_pvt', 'auction_enf', 'city']),
                ]
            if domain:
                matching = self.env['bussma.marketing'].search(
                    [('id', '=', self.marketing_id.id)] + domain
                )
                if not matching:
                    self.marketing_id = False
                    self.marketing_material_id = False


    # ─────────────────────────────────────────────
    # Notification & Activity Helpers for Stages
    # ─────────────────────────────────────────────
    def _get_stage_target_users(self, stage_selection):
        """
        Get target users to notify for a given financial stage selection.
        """
        self.ensure_one()
        users = self.env['res.users']

        if stage_selection == 'fin_marketing_mgr':
            # 1. Marketing Manager / Supervisors ONLY
            mkt_sup_group = self.env.ref('marketing_opportunity_management.group_marketing_supervisor', raise_if_not_found=False)
            if mkt_sup_group:
                users |= mkt_sup_group.users.filtered(lambda u: u.active)

        elif stage_selection == 'fin_sector_accountant':
            # 2. Commercial Sector Accountant
            sec_acc_group = self.env.ref('sales_and_auction_management.group_commercial_sector_accountant', raise_if_not_found=False)
            if sec_acc_group:
                users |= sec_acc_group.users.filtered(lambda u: u.active)

        elif stage_selection == 'fin_dept_mgr':
            # 3. Department Manager: Sales Manager, Auctions Manager, or Marketing Supervisor based on department
            if self.department == 'direct_sales':
                sales_mgr_group = self.env.ref('bussma_system.group_sales_manager', raise_if_not_found=False)
                if sales_mgr_group:
                    users |= sales_mgr_group.users.filtered(lambda u: u.active)
            elif self.department == 'auctions':
                auctions_mgr_group = self.env.ref('bussma_system.group_auctions_manager', raise_if_not_found=False)
                if auctions_mgr_group:
                    users |= auctions_mgr_group.users.filtered(lambda u: u.active)
            elif self.department == 'marketing':
                mkt_sup_group = self.env.ref('marketing_opportunity_management.group_marketing_supervisor', raise_if_not_found=False)
                if mkt_sup_group:
                    users |= mkt_sup_group.users.filtered(lambda u: u.active)

        elif stage_selection == 'fin_sector_mgr':
            # 4. Commercial Sector Manager
            sec_mgr_group = self.env.ref('bussma_system.group_commercial_sector_manager', raise_if_not_found=False)
            if sec_mgr_group:
                users |= sec_mgr_group.users.filtered(lambda u: u.active)

        elif stage_selection in ['fin_admin_accountant', 'fin_attach_receipts']:
            # 5 & 7. Financial Management Accountant
            admin_acc_group = self.env.ref('financial_management.group_financial_management_accountant', raise_if_not_found=False)
            if admin_acc_group:
                users |= admin_acc_group.users.filtered(lambda u: u.active)

        elif stage_selection == 'fin_financial_mgr':
            # 6. Financial Management Manager
            fin_mgr_group = self.env.ref('financial_management.group_financial_management', raise_if_not_found=False)
            if fin_mgr_group:
                users |= fin_mgr_group.users.filtered(lambda u: u.active)

        return users

    def create_mail_activity(self, users, summary=False, is_done=True):
        """Create Odoo activities for the specified users on this financial request record (same pattern as entries)."""
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
                self.env['mail.activity'].sudo().with_context(
                    mail_activity_quick_update=True,
                    mail_create_nosubscribe=True,
                ).create({
                    'summary': summary,
                    'activity_type_id': activity_type.id if activity_type else False,
                    'res_model_id': model_id,
                    'res_id': self.id,
                    'user_id': user.id,
                })

    def _notify_stage_authorized_users(self):
        """
        Create activities for internal notifications when moving across stages (2-8),
        and send email notification when arriving at archived stage (9).
        Follows the exact same approach as entries.
        """
        for rec in self:
            stage_sel = rec.financial_stage_selection
            if not stage_sel:
                continue

            # Always clear old activities when the stage changes (exact pattern as entries)
            rec.create_mail_activity(users=False, is_done=True)

            # If Archived: Send Email to all involved users + requester_id
            if stage_sel == 'fin_archived':
                all_involved_users = rec.env['res.users']
                if rec.requester_id and rec.requester_id.active:
                    all_involved_users |= rec.requester_id

                previous_stages = [
                    'fin_marketing_mgr', 'fin_sector_accountant', 'fin_dept_mgr',
                    'fin_sector_mgr', 'fin_admin_accountant', 'fin_financial_mgr',
                    'fin_attach_receipts'
                ]
                for p_stage in previous_stages:
                    all_involved_users |= rec._get_stage_target_users(p_stage)

                recipient_emails = {u.email.strip() for u in all_involved_users if u.email and u.email.strip()}
                if recipient_emails:
                    template = rec.env.ref('financial_management.email_template_financial_request_archived', raise_if_not_found=False)
                    if template:
                        email_to = ','.join(recipient_emails)
                        try:
                            template.send_mail(
                                rec.id,
                                email_values={'email_to': email_to},
                                force_send=True
                            )
                        except Exception as e:
                            _logger.error("[Financial Request Email] Failed to send archived email for request ID %s: %s", rec.id, str(e))
                continue

            # For internal notification stages (2 to 8): create background activity without chatter clutter
            target_users = rec._get_stage_target_users(stage_sel)
            if target_users:
                rec.create_mail_activity(users=target_users, summary=False, is_done=False)
    # ─────────────────────────────────────────────
    # Create: auto-sequence & stage assignment
    # ─────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', '/') == '/':
                vals['code'] = self.env['ir.sequence'].next_by_code(
                    'financial.request'
                ) or '/'
        records = super().create(vals_list)
        mkt_stage = self.env.ref('financial_management.stage_fin_marketing_mgr', raise_if_not_found=False)
        is_created_from_marketing = bool(
            self.env.context.get('default_marketing_id')
            or self.env.context.get('default_marketing_material_id')
        )
        if mkt_stage and is_created_from_marketing:
            for rec in records:
                if rec.marketing_material_id or rec.marketing_id or rec.department == 'marketing':
                    rec.stage_id = mkt_stage.id
        for rec in records:
            rec._update_attachment_names()
            rec._notify_stage_authorized_users()
        return records

    def _update_attachment_names(self):
        """ Prepend request code to attachment names for iban, tax_invoice, and receipt attachments. """
        for rec in self:
            if not rec.code or rec.code == '/':
                continue
            attachments = (
                rec.iban_attachment_ids |
                rec.tax_invoice_attachment_ids |
                rec.receipt_attachment_ids
            )
            for att in attachments:
                if att.name and rec.code not in att.name:
                    att.sudo().write({'name': f"{rec.code} - {att.name}"})

    def _check_receipts_count(self):
        """
        Verify that uploaded receipt attachments match receipts_count:
        - In fin_attach_receipts: uploaded_count cannot exceed receipts_count (if receipts_count > 0).
        - In fin_archived: receipts_count must be at least 1, and uploaded_count must equal receipts_count.
        """
        for rec in self:
            if rec.financial_stage_selection == 'fin_attach_receipts':
                if rec.receipts_count > 0:
                    uploaded_count = len(rec.receipt_attachment_ids)
                    if uploaded_count > rec.receipts_count:
                        raise UserError(
                            _("The number of uploaded attachments (%s) exceeds the specified number of receipts (%s). Please attach attachments matching the specified number of receipts only (%s).")
                            % (uploaded_count, rec.receipts_count, rec.receipts_count)
                        )
            elif rec.financial_stage_selection == 'fin_archived':
                if rec.receipts_count <= 0:
                    raise UserError(
                        _("The number of receipts must be at least 1.")
                    )
                uploaded_count = len(rec.receipt_attachment_ids)
                if uploaded_count != rec.receipts_count:
                    raise UserError(
                        _("The number of uploaded attachments (%s) does not match the specified number of receipts (%s). Please attach attachments matching the specified number of receipts only (%s).")
                        % (uploaded_count, rec.receipts_count, rec.receipts_count)
                    )

    def write(self, vals):
        stage_changed = 'stage_id' in vals
        res = super().write(vals)
        self._update_attachment_names()
        self._check_receipts_count()
        if stage_changed:
            self._notify_stage_authorized_users()
        return res

    def _get_mail_thread_data_attachments(self):
        """ Exclude attachments belonging to explicit model fields from the Chatter attachment popover (📎 button). """
        res = super()._get_mail_thread_data_attachments()
        if self:
            self.ensure_one()
            field_attachment_ids = set()
            for field_name in [
                'iban_attachment_ids',
                'tax_invoice_attachment_ids',
                'receipt_attachment_ids',
            ]:
                if hasattr(self, field_name):
                    attachments = getattr(self, field_name)
                    if attachments:
                        field_attachment_ids.update(attachments.ids)

            if field_attachment_ids:
                res = res.filtered(lambda a: a.id not in field_attachment_ids)
        return res


    # ─────────────────────────────────────────────
    # Permission helper
    # ─────────────────────────────────────────────
    def _check_financial_manager_permission(self):
        user = self.env.user
        if not (
            user.has_group('base.group_system') or
            user.has_group('financial_management.group_financial_management')
        ):
            raise UserError(_("Sorry, this action is restricted to Financial Management Manager only."))

    # ─────────────────────────────────────────────
    # Stage transition actions
    # ─────────────────────────────────────────────
    def _move_to_stage(self, xml_id):
        """Helper to move all records in self to a given stage by xml_id."""
        stage = self.env.ref(xml_id, raise_if_not_found=False)
        if not stage:
            raise UserError(_("The requested stage was not found."))
        for rec in self:
            rec.write({'stage_id': stage.id})

    def action_submit_to_marketing_manager(self):
        """Request Submission -> Marketing Manager Approval"""
        for rec in self:
            rec.write({
                'is_returned': False,
                'return_notes': False,
            })
        self._move_to_stage('financial_management.stage_fin_marketing_mgr')

    # Stage 2: Marketing Manager
    def action_approve_marketing_manager(self):
        """Marketing Manager Approval -> Commercial Sector Accountant Approval"""
        for rec in self:
            if rec.marketing_mgr_approval != 'approved':
                raise UserError(_("You must select 'Approved' to proceed to the next stage."))
            rec.write({
                'is_returned': False,
                'return_notes': False,
            })
        self._move_to_stage('financial_management.stage_fin_sector_accountant')

    def action_reject_marketing_manager(self):
        """Reject Marketing Manager Approval -> Return to Request Submission"""
        for rec in self:
            if rec.marketing_mgr_approval != 'rejected':
                raise UserError(_("You must select 'Rejected' to return the request."))
            if not rec.marketing_mgr_notes:
                raise UserError(_("Please write Marketing Manager notes explaining the reason for returning."))
            rec.write({
                'return_notes': rec.marketing_mgr_notes,
                'is_returned': True,
                'marketing_mgr_approval': False,
            })
        self._move_to_stage('financial_management.stage_fin_draft')

    # Stage 3: Sector Accountant
    def action_approve_sector_accountant(self):
        """Commercial Sector Accountant Approval -> Department Manager Approval"""
        for rec in self:
            if rec.sector_accountant_approval != 'approved':
                raise UserError(_("You must select 'Approved' to proceed to the next stage."))
            rec.write({
                'is_returned': False,
                'return_notes': False,
            })
        self._move_to_stage('financial_management.stage_fin_dept_mgr')

    def action_reject_sector_accountant(self):
        """Reject Commercial Sector Accountant Approval -> Return to Marketing Manager Approval"""
        for rec in self:
            if rec.sector_accountant_approval != 'rejected':
                raise UserError(_("You must select 'Rejected' to return the request."))
            if not rec.sector_accountant_notes:
                raise UserError(_("Please write Commercial Sector Accountant notes explaining the reason for returning."))
            rec.write({
                'return_notes': rec.sector_accountant_notes,
                'is_returned': True,
                'sector_accountant_approval': False,
            })
        self._move_to_stage('financial_management.stage_fin_marketing_mgr')

    # Stage 4: Department Manager
    def action_approve_dept_manager(self):
        """Department Manager Approval -> Commercial Sector Manager Approval"""
        for rec in self:
            if rec.dept_mgr_approval != 'approved':
                raise UserError(_("You must select 'Approved' to proceed to the next stage."))
            rec.write({
                'is_returned': False,
                'return_notes': False,
            })
        self._move_to_stage('financial_management.stage_fin_sector_mgr')

    def action_reject_dept_manager(self):
        """Reject Department Manager Approval -> Return to Commercial Sector Accountant Approval"""
        for rec in self:
            if rec.dept_mgr_approval != 'rejected':
                raise UserError(_("You must select 'Rejected' to return the request."))
            if not rec.dept_mgr_notes:
                raise UserError(_("Please write Department Manager notes explaining the reason for returning."))
            rec.write({
                'return_notes': rec.dept_mgr_notes,
                'is_returned': True,
                'dept_mgr_approval': False,
            })
        self._move_to_stage('financial_management.stage_fin_sector_accountant')

    # Stage 5: Sector Manager
    def action_approve_sector_manager(self):
        """Commercial Sector Manager Approval -> Administration Accountant Approval"""
        for rec in self:
            if rec.sector_mgr_approval != 'approved':
                raise UserError(_("You must select 'Approved' to proceed to the next stage."))
            rec.write({
                'is_returned': False,
                'return_notes': False,
            })
        self._move_to_stage('financial_management.stage_fin_admin_accountant')

    def action_reject_sector_manager(self):
        """Reject Commercial Sector Manager Approval -> Return to Department Manager Approval"""
        for rec in self:
            if rec.sector_mgr_approval != 'rejected':
                raise UserError(_("You must select 'Rejected' to return the request."))
            if not rec.sector_mgr_notes:
                raise UserError(_("Please write Commercial Sector Manager notes explaining the reason for returning."))
            rec.write({
                'return_notes': rec.sector_mgr_notes,
                'is_returned': True,
                'sector_mgr_approval': False,
            })
        self._move_to_stage('financial_management.stage_fin_dept_mgr')

    # Stage 6: Admin Accountant
    def action_approve_admin_accountant(self):
        """Administration Accountant Approval -> Financial Management Manager Approval"""
        for rec in self:
            if rec.admin_accountant_approval != 'approved':
                raise UserError(_("You must select 'Approved' to proceed to the next stage."))
            rec.write({
                'is_returned': False,
                'return_notes': False,
            })
        self._move_to_stage('financial_management.stage_fin_financial_mgr')

    def action_reject_admin_accountant(self):
        """Reject Administration Accountant Approval -> Return to Commercial Sector Manager Approval"""
        for rec in self:
            if rec.admin_accountant_approval != 'rejected':
                raise UserError(_("You must select 'Rejected' to return the request."))
            if not rec.admin_accountant_notes:
                raise UserError(_("Please write Administration Accountant notes explaining the reason for returning."))
            rec.write({
                'return_notes': rec.admin_accountant_notes,
                'is_returned': True,
                'admin_accountant_approval': False,
            })
        self._move_to_stage('financial_management.stage_fin_sector_mgr')

    # Stage 7: Financial Manager
    def action_approve_financial_manager(self):
        """Financial Management Manager Approval -> Attach Receipts"""
        for rec in self:
            if rec.financial_mgr_approval != 'approved':
                raise UserError(_("You must select 'Approved' to proceed to the next stage."))
            rec.write({
                'is_returned': False,
                'return_notes': False,
            })
        self._move_to_stage('financial_management.stage_fin_attach_receipts')

    def action_reject_financial_manager(self):
        """Reject Financial Management Manager Approval -> Return to Administration Accountant Approval"""
        for rec in self:
            if rec.financial_mgr_approval != 'rejected':
                raise UserError(_("You must select 'Rejected' to return the request."))
            if not rec.financial_mgr_notes:
                raise UserError(_("Please write Financial Management Manager notes explaining the reason for returning."))
            rec.write({
                'return_notes': rec.financial_mgr_notes,
                'is_returned': True,
                'financial_mgr_approval': False,
            })
        self._move_to_stage('financial_management.stage_fin_admin_accountant')

    # Stage 8: Attach Receipts
    def action_submit_receipts(self):
        """Attach Receipts -> Archive"""
        for rec in self:
            rec.write({
                'is_returned': False,
                'return_notes': False,
            })
        self._move_to_stage('financial_management.stage_fin_archived')
