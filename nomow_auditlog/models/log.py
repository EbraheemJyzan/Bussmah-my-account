# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, _
from odoo.exceptions import UserError
import ast
from datetime import datetime


class AuditlogLog(models.Model):
    _name = "auditlog.log"
    _description = "Auditlog - Log"
    _order = "create_date desc"

    name = fields.Char("Resource Name", size=64)
    model_id = fields.Many2one(
        "ir.model", string="Model", index=True, ondelete="set null"
    )
    model_name = fields.Char(readonly=True)
    model_model = fields.Char(string="Technical Model Name", readonly=True)
    res_id = fields.Integer("Resource ID")
    user_id = fields.Many2one("res.users", string="User")
    method = fields.Char(size=64)
    method_type = fields.Selection(
        [("create", "Create"), ("write", "Write"), ("unlink", "Unlink")],
        string="Method Type",
        store=True,
        compute="_compute_method_type",
    )
    line_ids = fields.One2many("auditlog.log.line", "log_id", string="Fields updated")
    http_session_id = fields.Many2one(
        "auditlog.http.session", string="Session", index=True
    )
    http_request_id = fields.Many2one(
        "auditlog.http.request", string="HTTP Request", index=True
    )
    ip_address = fields.Char(related="http_request_id.ip_address", string="IP Address", readonly=True, store=True)
    browser = fields.Char(related="http_request_id.browser", string="Browser", readonly=True, store=True)
    os = fields.Char(related="http_request_id.os", string="OS", readonly=True, store=True)
    log_type = fields.Selection(
        [("full", "Full log"), ("fast", "Fast log")], string="Type"
    )
    log_create_id = fields.Many2one('auditlog.log',compute="_get_log_create_id", string="Creation log")
    log_create_user_id = fields.Many2one(related="log_create_id.user_id", string="Creation User", readonly=True)
    log_create_date = fields.Datetime(related="log_create_id.create_date", string="Creation Log Date", readonly=True)
    log_create_line_ids = fields.One2many(related="log_create_id.line_ids", string="Creation Field Changes", readonly=True)
    log_write_ids = fields.One2many('auditlog.log',compute="_get_log_write_ids", string="Edit log")
    is_store = fields.Boolean(string="Is Restored")
    restored_res_id = fields.Integer(string="Restored Record ID", readonly=True)
    record_exists = fields.Boolean(compute="_compute_record_exists", string="Record Exists")

    @api.depends("model_id", "model_model", "res_id", "method_type", "is_store", "restored_res_id")
    def _compute_record_exists(self):
        for log in self:
            log.record_exists = False
            target_res_id = log.res_id
            if log.method_type == "unlink":
                if log.is_store and log.restored_res_id:
                    target_res_id = log.restored_res_id
                else:
                    continue
            model_name = log.model_model or (log.model_id.model if log.model_id else None)
            if not isinstance(model_name, str) or not target_res_id:
                continue
            if model_name in self.env:
                try:
                    record = self.env[model_name].sudo().browse(target_res_id)
                    log.record_exists = bool(record.exists())
                except Exception:
                    log.record_exists = False

    def action_open_record(self):
        self.ensure_one()
        if not self.record_exists:
            raise UserError(_("The target record no longer exists or has been deleted."))
        target_res_id = self.restored_res_id if (self.method_type == "unlink" and self.restored_res_id) else self.res_id
        return {
            "type": "ir.actions.act_window",
            "res_model": self.model_model,
            "res_id": target_res_id,
            "views": [(False, "form")],
            "target": "current",
        }
    
    def _get_log_create_id(self):
        for record in self:
            model = record.model_model or (record.model_id.model if record.model_id else False)
            if not record.res_id or not model:
                record.log_create_id = False
                continue
            record.log_create_id = record.env['auditlog.log'].search([
                ('res_id', '=', record.res_id),
                ('method', '=', 'create'),
                '|', ('model_model', '=', model), ('model_id.model', '=', model),
            ], limit=1)
    
    def _get_log_write_ids(self):
        for record in self:
            model = record.model_model or (record.model_id.model if record.model_id else False)
            if not record.res_id or not model:
                record.log_write_ids = False
                continue
            record.log_write_ids = record.env['auditlog.log'].search([
                ('res_id', '=', record.res_id),
                ('method', '=', 'write'),
                '|', ('model_model', '=', model), ('model_id.model', '=', model),
            ])
    
    @api.depends("method")
    def _compute_method_type(self):
        """Compute the method_type field based on the method value."""
        for record in self:
            if record.method == "create":
                record.method_type = "create"
            elif record.method == "write":
                record.method_type = "write"
            elif record.method == "unlink":
                record.method_type = "unlink"
            else:
                record.method_type = False
                
    @api.model_create_multi
    def create(self, vals_list):
        """Insert model_name and model_model field values upon creation."""
        for vals in vals_list:
            if not vals.get("model_id"):
                raise UserError(_("No model defined to create log."))
            model = self.env["ir.model"].sudo().browse(vals["model_id"])
            vals.update({"model_name": model.name, "model_model": model.model})
        return super().create(vals_list)

    def write(self, vals):
        """Update model_name and model_model field values to reflect model_id
        changes."""
        if "model_id" in vals:
            if not vals["model_id"]:
                raise UserError(_("The field 'model_id' cannot be empty."))
            model = self.env["ir.model"].sudo().browse(vals["model_id"])
            vals.update({"model_name": model.name, "model_model": model.model})
        return super().write(vals)

    @api.model
    def _extract_ids_from_value(self, value):
        """Extract integer IDs from various representations (ints, lists, tuples, commands, strings)."""
        ids = []
        if not value:
            return ids
        parsed = value
        if isinstance(value, str):
            val_str = value.strip()
            if not val_str or val_str in ('False', 'None', '[]', '()'):
                return ids
            try:
                parsed = ast.literal_eval(val_str)
            except Exception:
                try:
                    import re
                    return [int(m) for m in re.findall(r'\b\d+\b', val_str)]
                except Exception:
                    return ids

        if isinstance(parsed, (int, float)):
            return [int(parsed)]
        if isinstance(parsed, (list, tuple, set)):
            for item in parsed:
                if isinstance(item, (int, float)):
                    ids.append(int(item))
                elif isinstance(item, (list, tuple)) and len(item) > 0:
                    if item[0] == 6 and len(item) >= 3 and isinstance(item[2], (list, tuple, set)):
                        for sub in item[2]:
                            if isinstance(sub, (int, float)):
                                ids.append(int(sub))
                    elif item[0] == 4 and len(item) >= 2 and isinstance(item[1], (int, float)):
                        ids.append(int(item[1]))
                    elif isinstance(item[0], (int, float)):
                        ids.append(int(item[0]))
        return list(dict.fromkeys(ids))

    def handle_one2many_fields(self, relation_field, res_id, relation):
        try:
            if not res_id or not relation:
                return False
            child_log = self.env['auditlog.log'].sudo().search([
                ('res_id', '=', res_id),
                ('method', '=', 'unlink'),
                '|', ('model_model', '=', relation), ('model_id.model', '=', relation),
            ], limit=1, order='id desc')

            if not child_log:
                child_log = self.env['auditlog.log'].sudo().search([
                    ('res_id', '=', res_id),
                    ('method', '=', 'create'),
                    '|', ('model_model', '=', relation), ('model_id.model', '=', relation),
                ], limit=1, order='id desc')

            if not child_log:
                return False

            child_data = child_log.restore_data_list()
            if not child_data:
                return False

            if relation_field and relation_field in child_data:
                del child_data[relation_field]

            # Filter fields to only valid fields on the relation model
            if relation in self.env:
                rel_fields = self.env[relation]._fields
                child_data = {
                    k: v for k, v in child_data.items()
                    if k in rel_fields and (not rel_fields[k].compute or rel_fields[k].inverse or rel_fields[k].store)
                }

            return child_data if child_data else False
        except Exception:
            return False

    def clean_field_value(self, line):
        ignore_fields = {
            'message_follower_ids', 'message_ids', 'message_attachment_count', 'activity_ids',
            'activity_state', 'create_uid', 'create_date', 'write_uid', 'write_date',
            '__last_update', 'message_has_error', 'message_has_sms_error', 'message_main_attachment_id',
            'website_message_ids', 'activity_user_id', 'activity_type_id', 'activity_summary',
            'activity_date_deadline', 'activity_exception_decoration', 'activity_exception_icon',
            'message_needaction', 'message_needaction_counter', 'message_has_error_counter', 'message_partner_ids',
            'invoice_line_ids', 'id',
        }
        if line.field_name in ignore_fields:
            return False

        model_name = self.model_model or (self.model_id.model if self.model_id else None)
        if model_name and model_name in self.env:
            if line.field_name not in self.env[model_name]._fields:
                return False
            odoo_field = self.env[model_name]._fields[line.field_name]
            if odoo_field.compute and not odoo_field.inverse and not odoo_field.store:
                return False

        # In unlink logs, the captured state before deletion is in old_value
        # In create/write logs, values are in new_value
        value = line.old_value if self.method_type == 'unlink' else (line.new_value if line.new_value is not False else line.old_value)
        value_text = line.old_value_text if self.method_type == 'unlink' else (line.new_value_text if line.new_value_text is not False else line.old_value_text)

        field = False
        if self.model_id:
            field = self.env['ir.model.fields'].search([
                ('model_id', '=', self.model_id.id),
                ('name', '=', line.field_name)
            ], limit=1)

        if not field and model_name:
            field = self.env['ir.model.fields'].search([
                ('model', '=', model_name),
                ('name', '=', line.field_name)
            ], limit=1)

        if not field:
            return False

        ttype = field.ttype

        if value in ('False', '', False, None, 'None'):
            if ttype in ('many2one', 'many2many', 'one2many') and value_text not in ('False', '', False, None, 'None'):
                value = value_text
            else:
                return False

        if ttype == 'boolean':
            return value in (True, 'True', '1', 1)

        if ttype in ('char', 'text', 'html'):
            return str(value)

        if ttype in ('integer',):
            try:
                return int(value)
            except Exception:
                return value

        if ttype in ('float', 'monetary'):
            try:
                return float(value)
            except Exception:
                return value

        if ttype == 'selection':
            return str(value)

        if ttype == 'date':
            if isinstance(value, datetime):
                return value.date()
            val_str = str(value).strip().split(' ')[0]
            try:
                datetime.strptime(val_str, '%Y-%m-%d')
                return val_str
            except Exception:
                return value

        if ttype == 'datetime':
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%d %H:%M:%S')
            val_str = str(value).strip().replace('T', ' ').split('.')[0]
            try:
                datetime.strptime(val_str, '%Y-%m-%d %H:%M:%S')
                return val_str
            except Exception:
                return value

        if ttype == 'many2one':
            rel_ids = self._extract_ids_from_value(value)
            if not rel_ids and value_text:
                rel_ids = self._extract_ids_from_value(value_text)
            if rel_ids:
                rel_id = rel_ids[0]
                if field.relation and field.relation in self.env:
                    if self.env[field.relation].sudo().browse(rel_id).exists():
                        return rel_id
                    return False
                return rel_id
            return False

        if ttype == 'many2many':
            ids_list = self._extract_ids_from_value(value)
            if not ids_list and value_text:
                ids_list = self._extract_ids_from_value(value_text)
            if ids_list:
                if field.relation and field.relation in self.env:
                    existing_ids = self.env[field.relation].sudo().browse(ids_list).exists().ids
                    if existing_ids:
                        return [(6, 0, existing_ids)]
                    return False
                return [(6, 0, ids_list)]
            return False

        if ttype == 'one2many':
            child_ids = self._extract_ids_from_value(value)
            if not child_ids and value_text:
                child_ids = self._extract_ids_from_value(value_text)

            if not child_ids:
                return False
            if not field.relation or field.relation not in self.env:
                return False

            data_one2many = []
            rel_model = self.env[field.relation].sudo()
            for child_id in child_ids:
                existing_child = rel_model.browse(child_id).exists()
                if existing_child:
                    # Child record exists in database: link it, DO NOT create a duplicate!
                    data_one2many.append((4, child_id))
                else:
                    # Child record was deleted from database: recreate it if captured in auditlog
                    child_data = self.handle_one2many_fields(field.relation_field, child_id, field.relation)
                    if child_data:
                        data_one2many.append((0, 0, child_data))
            return data_one2many if data_one2many else False

        return value

    def restore_data_list(self):
        """Prepare record data dictionary for restoration."""
        data = {}
        # 1. Primary: if this log has captured lines (especially unlink log)
        if self.line_ids:
            for line in self.line_ids:
                val = self.clean_field_value(line)
                if val not in (False, None):
                    data[line.field_name] = val

        # 2. Fallback: if no line_ids on this log, check log_create_id + log_write_ids
        if not data:
            if self.log_create_id and not self.is_store:
                for line in self.log_create_id.line_ids:
                    val = self.clean_field_value(line)
                    if val not in (False, None):
                        data[line.field_name] = val

            if self.log_write_ids and not self.is_store:
                sorted_logs = sorted(self.log_write_ids, key=lambda rec: rec.create_date or datetime.min)
                for record in sorted_logs:
                    for line in record.line_ids:
                        val = self.clean_field_value(line)
                        if val not in (False, None):
                            data[line.field_name] = val

        # Sanitize data to ensure all keys belong to the target model
        model_name = self.model_model or (self.model_id.model if self.model_id else None)
        if model_name and model_name in self.env:
            model_fields = self.env[model_name]._fields
            data = {
                k: v for k, v in data.items()
                if k in model_fields and (not model_fields[k].compute or model_fields[k].inverse or model_fields[k].store)
            }
        return data

    def restore_create(self):
        model_name = self.model_model or (self.model_id.model if self.model_id else None)
        if not model_name or model_name not in self.env:
            raise UserError(_("Model '%s' does not exist in the system.") % model_name)

        data = self.restore_data_list()
        if not data:
            raise UserError(_("No captured field data found to restore record '%s' (ID %s).") % (self.name or model_name, self.res_id))

        try:
            record_create = self.env[model_name].sudo().with_context(
                tracking_disable=True,
                mail_create_nosubscribe=True,
                auditlog_disabled=True,
            ).create(data)

            # Ensure existing one2many child records linked via (4, id) correctly reference record_create
            for fname, fvals in data.items():
                field_obj = record_create._fields.get(fname)
                if field_obj and field_obj.type == 'one2many' and field_obj.inverse_name:
                    if isinstance(fvals, list):
                        linked_ids = [
                            cmd[1] for cmd in fvals
                            if isinstance(cmd, (list, tuple)) and len(cmd) >= 2 and cmd[0] == 4
                        ]
                        if linked_ids:
                            comodel = self.env[field_obj.comodel_name].sudo()
                            missing_rel = comodel.browse(linked_ids).filtered(
                                lambda r: r.exists() and r[field_obj.inverse_name] != record_create
                            )
                            if missing_rel:
                                missing_rel.write({field_obj.inverse_name: record_create.id})
        except Exception as e:
            raise UserError(_("Failed to restore record of model '%s': %s") % (model_name, str(e)))

        self.write({
            'is_store': True,
            'restored_res_id': record_create.id,
        })
        return {
            'name': _("Restored Record"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': model_name,
            'res_id': record_create.id,
            'target': 'current',
        }

    def check_duplicate_display_name(self):
        """Check if an existing record in the target model already has the same display_name."""
        self.ensure_one()
        model_name = self.model_model or (self.model_id.model if self.model_id else None)
        if not model_name or model_name not in self.env:
            return False, False

        model_obj = self.env[model_name]
        target_name = self.name
        if not target_name:
            data = self.restore_data_list()
            target_name = data.get('name') or data.get('display_name')

        if not target_name:
            return False, False

        existing = False
        try:
            existing = model_obj.sudo().search([('display_name', '=', target_name)], limit=1)
        except Exception:
            rec_name = getattr(model_obj, '_rec_name', 'name') or 'name'
            if rec_name in model_obj._fields:
                try:
                    existing = model_obj.sudo().search([(rec_name, '=', target_name)], limit=1)
                except Exception:
                    existing = False

        return bool(existing), target_name

    def restore_write(self):
        return True

    def restore_data(self):
        # 1. Check for duplicate display_name if not force_restore
        if not self.env.context.get('force_restore'):
            if len(self) == 1:
                record = self[0]
                if record.method_type == 'unlink':
                    has_dup, target_name = record.check_duplicate_display_name()
                    if has_dup:
                        wizard = self.env['auditlog.restore.confirm.wizard'].create({
                            'log_ids': [(6, 0, self.ids)],
                            'message': _("This record name ('%s') already exists. Do you want to continue restoring this record?") % target_name,
                        })
                        return {
                            'name': _("Restore Confirmation"),
                            'type': 'ir.actions.act_window',
                            'res_model': 'auditlog.restore.confirm.wizard',
                            'res_id': wizard.id,
                            'view_mode': 'form',
                            'target': 'new',
                        }
            elif len(self) > 1:
                dup_names = []
                for record in self:
                    if record.method_type == 'unlink':
                        has_dup, t_name = record.check_duplicate_display_name()
                        if has_dup and t_name:
                            dup_names.append(t_name)
                if dup_names:
                    names_str = ", ".join(f"'{n}'" for n in dup_names[:5])
                    if len(dup_names) > 5:
                        names_str += f" (+{len(dup_names) - 5})"
                    wizard = self.env['auditlog.restore.confirm.wizard'].create({
                        'log_ids': [(6, 0, self.ids)],
                        'message': _("There are current records with the same names (%s). Do you want to continue restoring them?") % names_str,
                    })
                    return {
                        'name': _("Restore Confirmation"),
                        'type': 'ir.actions.act_window',
                        'res_model': 'auditlog.restore.confirm.wizard',
                        'res_id': wizard.id,
                        'view_mode': 'form',
                        'target': 'new',
                    }

        # 2. Proceed with restoration
        record_create_action = False
        restored_count = 0
        for record in self:
            if record.method_type == 'unlink':
                if record.is_store and record.record_exists:
                    raise UserError(_("This record (ID %s) has already been restored.") % record.res_id)
                record_create_action = record.sudo().restore_create()
                restored_count += 1

        if not record_create_action:
            raise UserError(_("No deleted records were restored. Ensure you select unlink logs with captured data."))

        if restored_count == 1:
            return record_create_action
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Success"),
                    'message': _("%s record(s) restored successfully.") % restored_count,
                    'sticky': False,
                    'type': 'success',
                }
            }


class AuditlogRestoreConfirmWizard(models.TransientModel):
    _name = "auditlog.restore.confirm.wizard"
    _description = "Auditlog - Restore Confirmation Wizard"

    log_ids = fields.Many2many("auditlog.log", string="Logs to Restore")
    message = fields.Text(string="Message", readonly=True)

    def action_confirm_restore(self):
        self.ensure_one()
        return self.log_ids.with_context(force_restore=True).restore_data()
