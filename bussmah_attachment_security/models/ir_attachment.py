# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError, AccessError

PROTECTED_MODULES = {
    'bussma_system',
    'financial_management',
    'helpdesk_ticket',
    'hr_requests',
    'marketing_opportunity_management',
    'sales_and_auction_management',
}

SPECIAL_PROTECTED_MODELS = {
    'bussma.opportunity.attachment',
    'bussma.marketing.request.wizard',
    'office.request.marketing.wizard',
    'sales.auction.request.wizard',
    'marketing.return.to.opportunity.wizard',
    'marketing.return.to.requste.wizard',
}

PARENT_RELATIONS = {
    # Marketing module hierarchy
    'bussma.marketing': [
        ('opportunity_id', 'bussma.opportunity'),
        ('office_request_id', 'office.request'),
        ('bussma_project_id', 'bussma.project'),
    ],
    'bussma.marketing.task': [
        ('material_id', 'bussma.marketing.material'),
        ('marketing_id', 'bussma.marketing'),
    ],
    'bussma.marketing.material': [
        ('marketing_id', 'bussma.marketing'),
    ],
    'bussma.material.return.note': [
        ('material_id', 'bussma.marketing.material'),
    ],
    'bussma.material.stage.history': [
        ('material_id', 'bussma.marketing.material'),
    ],
    'bussma.opportunity': [
        ('marketing_id', 'bussma.marketing'),
        ('marketing_ids', 'bussma.marketing'),
    ],
    'entries': [
        ('opportunity_id', 'bussma.opportunity'),
    ],
    'entries.stage.history': [
        ('entry_id', 'entries'),
    ],
    'entries.return.log': [
        ('entry_id', 'entries'),
    ],
    'office.request': [
        ('marketing_id', 'bussma.marketing'),
    ],
    'bussma.project': [
        ('marketing_id', 'bussma.marketing'),
    ],
    # Sales and Auction
    'auction.manager.approval': [
        ('auction_id', 'sales.auction.management'),
    ],
    'sales.manager.approval': [
        ('auction_id', 'sales.auction.management'),
    ],
}


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    # ----------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------

    @api.model
    def _get_protected_models(self):
        """
        Returns the set of model names belonging to PROTECTED_MODULES.
        Cached on the registry to avoid repeated lookups.
        """
        if not hasattr(self.env.registry, '_bussmah_protected_models'):
            protected = set()
            for model_name, model_obj in self.env.registry.models.items():
                if getattr(model_obj, '_module', '') in PROTECTED_MODULES:
                    protected.add(model_name)
            self.env.registry._bussmah_protected_models = protected
        return self.env.registry._bussmah_protected_models

    def _get_m2m_parent_records(self):
        """Find parent records linked to this attachment via Many2many fields."""
        self.ensure_one()
        parents = []
        cr = self.env.cr

        # 1. Opportunity
        cr.execute("SELECT opp_id FROM bussma_opportunity_attachment_rel WHERE attachment_id = %s", [self.id])
        for row in cr.fetchall():
            parents.append(('bussma.opportunity', row[0]))
        cr.execute("SELECT opp_id FROM bussma_opportunity_return_attachment_rel WHERE attachment_id = %s", [self.id])
        for row in cr.fetchall():
            parents.append(('bussma.opportunity', row[0]))

        # 2. Project
        cr.execute("SELECT project_id FROM bussma_project_mkt_return_att_rel WHERE att_id = %s", [self.id])
        for row in cr.fetchall():
            parents.append(('bussma.project', row[0]))

        # 3. Office Request
        cr.execute("SELECT req_id FROM office_req_return_att_rel WHERE att_id = %s", [self.id])
        for row in cr.fetchall():
            parents.append(('office.request', row[0]))

        # 4. Marketing Request
        cr.execute("SELECT mkt_id FROM bussma_marketing_attachments_request_rel WHERE att_id = %s", [self.id])
        for row in cr.fetchall():
            parents.append(('bussma.marketing', row[0]))
        cr.execute("SELECT mkt_id FROM bussma_marketing_return_attachment_rel WHERE attachment_id = %s", [self.id])
        for row in cr.fetchall():
            parents.append(('bussma.marketing', row[0]))

        return parents

    def _is_protected_attachment(self):
        """Return True if this attachment belongs to a record from a protected module."""
        self.ensure_one()
        if self.res_model:
            if self.res_model in SPECIAL_PROTECTED_MODELS or self.res_model in self._get_protected_models():
                return True
            # Fallback: check via ir.model database entry
            ir_model = self.env['ir.model'].sudo().search(
                [('model', '=', self.res_model)], limit=1
            )
            if ir_model and ir_model.modules:
                mod_set = set(m.strip() for m in ir_model.modules.split(','))
                if mod_set & PROTECTED_MODULES:
                    return True

        if self._get_m2m_parent_records():
            return True

        return False

    @api.model
    def _user_can_access_record(self, model_name, rec_id, user):
        """
        Check whether *user* can read (model_name, rec_id).
        Uses sudo to browse the record, then checks access in user context.
        Returns True/False without raising.
        """
        if model_name not in self.env:
            return True  # Unknown model: don't block
        try:
            if self.env[model_name].is_transient():
                return True  # Transient/wizard records: always allow
        except Exception:
            pass
        try:
            record = self.env[model_name].sudo().browse(rec_id)
            if not record.exists():
                return True  # Deleted record: allow
            record.with_user(user).check_access('read')
            return True
        except (AccessError, UserError):
            return False

    @api.model
    def _user_can_access_via_parents(self, model_name, rec_id, user, _visited=None):
        """
        Check whether *user* has indirect access to (model_name, rec_id)
        through any parent record defined in PARENT_RELATIONS.
        _visited prevents infinite loops.
        """
        if _visited is None:
            _visited = set()
        key = (model_name, rec_id)
        if key in _visited:
            return False
        _visited.add(key)

        parents = PARENT_RELATIONS.get(model_name, [])
        if not parents:
            return False

        try:
            record_sudo = self.env[model_name].sudo().browse(rec_id)
            if not record_sudo.exists():
                return False
        except Exception:
            return False

        for field_name, parent_model in parents:
            if field_name not in record_sudo._fields:
                continue
            try:
                parent_val = record_sudo[field_name]
            except Exception:
                continue
            if not parent_val:
                continue
            # Many2one -> 1 record; One2many/Many2many -> multiple
            for parent_rec in parent_val.sudo():
                if not parent_rec.exists():
                    continue
                parent_id = parent_rec.id
                if self._user_can_access_record(parent_model, parent_id, user):
                    return True
                # One level of grandparents
                if self._user_can_access_via_parents(
                        parent_model, parent_id, user, _visited):
                    return True

        return False

    @api.model
    def _user_authorized_for_protected_att(self, att_sudo, user):
        """
        Main authorization check for a single protected attachment.
        Logic:
          1. Check M2M parent records (Opportunities, Projects, Office Requests, Marketing)
          2. No res_model/res_id  -> allow (wizard/orphaned attachment)
          3. Direct access on linked record  -> allow
          4. Access via a parent record  -> allow
          5. Otherwise -> deny
        """
        # 1. Check Many2many parent records
        m2m_parents = att_sudo._get_m2m_parent_records()
        if m2m_parents:
            for parent_model, parent_id in m2m_parents:
                if self._user_can_access_record(parent_model, parent_id, user):
                    return True
                if self._user_can_access_via_parents(parent_model, parent_id, user):
                    return True
            if att_sudo.res_model in SPECIAL_PROTECTED_MODELS and not att_sudo.res_id:
                return False

        res_model = att_sudo.res_model
        res_id = att_sudo.res_id

        if not res_model or not res_id:
            return True

        if self._user_can_access_record(res_model, res_id, user):
            return True

        if self._user_can_access_via_parents(res_model, res_id, user):
            return True

        return False

    # ----------------------------------------------------------
    # Override Odoo access-check entry points
    # ----------------------------------------------------------

    def _check_access(self, operation: str):
        """Override: apply custom logic for protected-module attachments."""
        if self.env.is_superuser():
            return None

        user = self.env.user
        if not user.has_group('base.group_user'):
            return super()._check_access(operation)

        if operation in ('read', 'create', 'write'):
            protected = self.sudo().filtered(lambda a: a._is_protected_attachment())
            non_protected = self - protected
            if non_protected:
                super(IrAttachment, non_protected)._check_access(operation)
            for att in protected:
                if not self._user_authorized_for_protected_att(att, user):
                    raise AccessError(
                        _("You do not have access to this attachment because "
                          "you have no access to the record it belongs to "
                          "(or any related parent record).")
                    )
            return None

        return super()._check_access(operation)

    @api.model
    def check(self, mode, values=None):
        """Override: apply custom logic for protected-module attachments."""
        if self.env.is_superuser():
            return True

        user = self.env.user
        if not user.has_group('base.group_user'):
            return super().check(mode, values=values)

        if mode in ('read', 'create', 'write'):
            if self:
                protected = self.sudo().filtered(lambda a: a._is_protected_attachment())
                non_protected = self - protected
                if non_protected:
                    super(IrAttachment, non_protected).check(mode, values=values)
                for att in protected:
                    if not self._user_authorized_for_protected_att(att, user):
                        raise AccessError(
                            _("You do not have access to this attachment because "
                              "you have no access to the record it belongs to "
                              "(or any related parent record).")
                        )
                return True

            # New attachment being created via values dict
            if values and values.get('res_model'):
                res_model = values['res_model']
                if res_model in self._get_protected_models() or res_model in SPECIAL_PROTECTED_MODELS:
                    res_id = values.get('res_id')
                    if res_id:
                        if not self._user_can_access_record(res_model, res_id, user):
                            if not self._user_can_access_via_parents(res_model, res_id, user):
                                raise AccessError(
                                    _("You cannot attach a file to this record "
                                      "because you have no access to it.")
                                )
                    return True

        return super().check(mode, values=values)

    def check_access_rule(self, operation):
        """Override: apply custom logic for protected-module attachments."""
        if self.env.is_superuser():
            return

        user = self.env.user
        if not user.has_group('base.group_user'):
            return super().check_access_rule(operation)

        if operation in ('read', 'create', 'write'):
            protected = self.sudo().filtered(lambda a: a._is_protected_attachment())
            non_protected = self - protected
            if non_protected:
                super(IrAttachment, non_protected).check_access_rule(operation)
            for att in protected:
                if not self._user_authorized_for_protected_att(att, user):
                    raise AccessError(
                        _("You do not have access to this attachment because "
                          "you have no access to the record it belongs to "
                          "(or any related parent record).")
                    )
            return

        super().check_access_rule(operation)

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        """
        Override: merge standard search results with protected-module
        attachments that this user is authorized to see via parent traversal.
        """
        if self.env.is_superuser():
            return super()._search(domain, offset=offset, limit=limit, order=order)

        user = self.env.user
        if not user.has_group('base.group_user'):
            return super()._search(domain, offset=offset, limit=limit, order=order)

        # Standard (restricted) search
        std_query = super()._search(domain, offset=0, limit=None, order=None)
        std_rows = self.env.execute_query(
            std_query.select(self._field_to_sql(self._table, 'id'))
        )
        allowed_ids = set(r[0] for r in std_rows)

        # Full search with superuser to find protected attachments we might add
        all_query = super(IrAttachment, self.sudo())._search(
            domain, offset=0, limit=None, order=None
        )
        all_rows = self.env.execute_query(
            all_query.select(self._field_to_sql(self._table, 'id'))
        )
        all_ids = set(r[0] for r in all_rows)

        missing_ids = all_ids - allowed_ids
        if missing_ids:
            for att in self.sudo().browse(missing_ids):
                if att._is_protected_attachment():
                    if self._user_authorized_for_protected_att(att, user):
                        allowed_ids.add(att.id)

        return self.env['ir.attachment'].sudo()._search(
            [('id', 'in', list(allowed_ids))],
            offset=offset, limit=limit, order=order,
        )

    def generate_access_token(self):
        """
        Override: for protected attachments where the current user is authorized
        (even if they are not the creator), generate the access token using sudo.

        This solves the HTML-download issue: Odoo's HTTP controller uses the
        access_token for a credential-free download (via sudo). When a non-creator
        authorized user first views the attachment, the token may not yet exist.
        Calling write({'access_token': ...}) in the normal flow would trigger
        check('write') on the parent record (bussma.opportunity etc.) which fails
        due to record-level rules for users not matching assigned_user_id.
        By using sudo here we bypass that constraint for authorized users.
        """
        if self.env.is_superuser():
            return super().generate_access_token()

        user = self.env.user
        if not user.has_group('base.group_user'):
            return super().generate_access_token()

        tokens = []
        for att in self:
            att_sudo = att.sudo()
            if (att_sudo._is_protected_attachment()
                    and self._user_authorized_for_protected_att(att_sudo, user)):
                # Ensure token exists, writing with sudo to bypass ACL/record-rules
                if not att_sudo.access_token:
                    att_sudo.write({'access_token': att_sudo._generate_access_token()})
                tokens.append(att_sudo.access_token)
            else:
                tokens.extend(super(IrAttachment, att).generate_access_token())
        return tokens

    def validate_access(self, access_token):
        """
        Override: for internal users accessing protected attachments they are
        authorized on (even without an access_token), return the sudo record so
        the HTTP controller can serve the file without further ORM-level checks.

        Without this, the base implementation returns ``self`` (user context) for
        internal users with no token, and the subsequent stream read triggers
        check('read') → check_access('read') on the parent model which fails for
        non-creator/non-assigned users due to record rules.
        """
        self.ensure_one()
        # If a valid access_token is provided, delegate entirely to super
        if access_token:
            return super().validate_access(access_token)

        user = self.env.user
        att_sudo = self.sudo()

        # For internal authorized users on protected attachments: serve via sudo
        if (user.has_group('base.group_user')
                and att_sudo._is_protected_attachment()
                and self._user_authorized_for_protected_att(att_sudo, user)):
            return att_sudo

        return super().validate_access(access_token)

    def unlink(self):
        """Restrict deletion of protected attachments to System Administrators."""
        if not self.env.is_superuser():
            user = self.env.user
            if not user.has_group('base.group_system'):
                for rec in self.sudo():
                    if rec._is_protected_attachment():
                        raise UserError(
                            _("Deleting attachments of protected records is restricted "
                              "to System Administrators only.")
                        )
        return super().unlink()
