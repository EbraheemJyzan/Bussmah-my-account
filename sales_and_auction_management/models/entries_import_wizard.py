# -*- coding: utf-8 -*-
import base64
import io
import json
import logging
import os
import re
from datetime import datetime, date

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

def hijri_to_gregorian(year, month, day):
    jd = int((11 * year + 3) / 30) + 354 * year + 30 * month - int((month - 1) / 2) + day + 1948440 - 385
    l = jd + 68569
    n = int((4 * l) / 146097)
    l = l - int((146097 * n + 3) / 4)
    i = int((4000 * (l + 1)) / 1464001)
    l = l - int((1461 * i) / 4) + 31
    j = int((80 * l) / 2447)
    d = l - int((2447 * j) / 80)
    l = int(j / 11)
    m = j + 2 - (12 * l)
    y = 100 * (n - 49) + i + l
    return date(y, m, d)

def gregorian_to_hijri(g_date):
    if not g_date:
        return False
    try:
        hy = int((g_date.year - 622) * 1.03078)
        g_ref = hijri_to_gregorian(hy, 1, 1)
        diff = (g_date - g_ref).days
        if diff < 0:
            hy -= 1
            g_ref = hijri_to_gregorian(hy, 1, 1)
            diff = (g_date - g_ref).days
        elif diff >= 355:
            g_next = hijri_to_gregorian(hy + 1, 1, 1)
            if g_date >= g_next:
                hy += 1
                g_ref = g_next
                diff = (g_date - g_ref).days

        hm = min(12, max(1, int(diff / 29.53) + 1))
        g_mref = hijri_to_gregorian(hy, hm, 1)
        hd = (g_date - g_mref).days + 1

        while hd < 1 and hm > 1:
            hm -= 1
            g_mref = hijri_to_gregorian(hy, hm, 1)
            hd = (g_date - g_mref).days + 1

        while hd > 30 and hm < 12:
            g_next_m = hijri_to_gregorian(hy, hm + 1, 1)
            if g_date >= g_next_m:
                hm += 1
                g_mref = g_next_m
                hd = (g_date - g_mref).days + 1
            else:
                break

        return f"{hy:04d}-{hm:02d}-{hd:02d}"
    except Exception:
        return False

def parse_date_value(raw_val):
    """
    Parse date value from Excel (Gregorian or Hijri).
    Returns (gregorian_date_object, hijri_string_or_False).
    """
    if not raw_val:
        return False, False
    if isinstance(raw_val, (datetime, date)):
        dt_val = raw_val if isinstance(raw_val, date) else raw_val.date()
        if dt_val.year < 1600:
            try:
                g_date = hijri_to_gregorian(dt_val.year, dt_val.month, dt_val.day)
                h_str = f"{dt_val.year:04d}-{dt_val.month:02d}-{dt_val.day:02d}"
                return g_date, h_str
            except Exception:
                return False, str(dt_val)
        return dt_val, gregorian_to_hijri(dt_val)

    val_str = str(raw_val).strip()
    if val_str.endswith('.0'):
        val_str = val_str[:-2]

    if not val_str:
        return False, False

    parts = re.findall(r'\d+', val_str)
    if len(parts) == 1 and len(val_str) == 8 and val_str.isdigit():
        parts = [val_str[:4], val_str[4:6], val_str[6:8]]

    if len(parts) >= 3:
        p1, p2, p3 = int(parts[0]), int(parts[1]), int(parts[2])
        if p1 > 1000:
            y, m, d = p1, p2, p3
        elif p3 > 1000:
            y = p3
            if p1 > 12:
                d, m = p1, p2
            elif p2 > 12:
                d, m = p2, p1
            else:
                d, m = p1, p2
        else:
            y, m, d = p1, p2, p3

        if 1300 <= y <= 1500:
            try:
                g_date = hijri_to_gregorian(y, m, d)
                h_str = f"{y:04d}-{m:02d}-{d:02d}"
                return g_date, h_str
            except Exception:
                return False, val_str
        elif 1900 <= y <= 2100:
            try:
                g_date = date(y, m, d)
                h_str = gregorian_to_hijri(g_date)
                return g_date, h_str
            except Exception:
                return False, val_str

    return False, val_str

# --------------------------------------------------------------------------- #
#  Column header mapping (Arabic label in the Excel → field name on 'entries') #
# --------------------------------------------------------------------------- #
COLUMN_MAP = {
    # Customer Section
    'رغبة العميل':              'customer_intent_rel',
    'رغبة العميل (rel)':        'customer_intent_rel',
    'customer_intent':          'customer_intent_rel',
    'customer_intent_rel':      'customer_intent_rel',
    'اسم العميل':              'partner_id',
    'اسم العميل/المالك':       'partner_id',
    'العميل':                  'partner_id',
    'صفة العميل':              'customer_role_rel',
    'صفة العميل (rel)':        'customer_role_rel',
    'customer_role':            'customer_role_rel',
    'customer_role_rel':        'customer_role_rel',
    'نوع المالك':              'owner_type',
    'رقم التواصل مع العميل':   'partner_mobile',
    'رقم التواصل':             'partner_mobile',
    'رقم الجوال':              'partner_mobile',
    'جوال العميل':             'partner_mobile',
    'هاتف العميل':             'partner_mobile',
    'الجوال':                  'partner_mobile',

    # Technical Offer
    'هل يتطلب عرض فني؟':       'requires_technical_offer',
    'هل يتطلب عرض فني':        'requires_technical_offer',
    'يتطلب عرض فني؟':          'requires_technical_offer',
    'يتطلب عرض فني':           'requires_technical_offer',
    'عرض فني':                 'requires_technical_offer',

    # Lister Section
    'اسم المدرج':              'entered_by_name',
    'المدرج':                  'entered_by_name',
    'ايميل المدرج':            'entered_by_email',
    'إيميل المدرج':            'entered_by_email',
    'بريد المدرج':             'entered_by_email',
    'البريد الإلكتروني للمدرج': 'entered_by_email',
    'البريد الالكتروني للمدرج': 'entered_by_email',

    # Property Section
    'نوع العقار':              'property_type',
    'استخدام العقار':          'property_usage_rel',
    'استخدام العقار (rel)':    'property_usage_rel',
    'property_usage':           'property_usage_rel',
    'property_usage_rel':       'property_usage_rel',

    'المساحة (م²)':            'area_sqm',
    'المساحة(م²)':             'area_sqm',
    'المساحة (م2)':            'area_sqm',
    'المساحة(م2)':             'area_sqm',
    'المساحة م²':              'area_sqm',
    'المساحة م2':              'area_sqm',
    'المساحة':                 'area_sqm',

    'سعر العميل (للمتر مربع)': 'customer_price_per_sqm',
    'سعر العميل(للمتر مربع)':  'customer_price_per_sqm',
    'سعر العميل للمتر مربع':   'customer_price_per_sqm',
    'سعر العميل (للمتر)':      'customer_price_per_sqm',
    'سعر العميل(للمتر)':       'customer_price_per_sqm',
    'سعر العميل للمتر':        'customer_price_per_sqm',
    'سعر العميل':              'customer_price_per_sqm',

    'هل يوجد دخل؟':            'has_income',
    'هل يوجد دخل':             'has_income',
    'هل يوجد دخل للعقار؟':     'has_income',
    'هل يوجد دخل للعقار':      'has_income',
    'يوجد دخل؟':               'has_income',
    'يوجد دخل':                'has_income',
    'الدخل الحالي':            'current_income',
    'قيمة الدخل الحالي':       'current_income',

    # Location Section
    'المدينة':                  'city',
    'الحي':                    'district_id',
    'الموقع (اللوكيشن)':       'location_url',
    'الموقع اللوكيشن':         'location_url',
    'الموقع':                  'location_url',
    'رقم القطعة':              'plot_number',
    'رقم المخطط':              'plan_number',
    'رقم الصك':                'deed_number',
    'تاريخ الصك':              'deed_date',
    'تاريخ الصك (هجري)':       'deed_date_hijri',
    'تاريخ الصك هجري':         'deed_date_hijri',
    'deed_date':                'deed_date',
    'deed_date_hijri':          'deed_date_hijri',
    'تاريخ الإدراج':            'listing_date',
    'تاريخ الادراج':            'listing_date',
    'listing_date':             'listing_date',

    # Notes
    'ملاحظات':                 'entered_notes',
}

# Allowed values for Selection fields (Arabic → technical key)
CUSTOMER_INTENT_MAP = {
    'بيع مباشر':             'direct_sale',
    'بيع':                  'direct_sale',
    'المبيعات':             'direct_sale',
    'المزادات':             'auction',
    'مزاد':                 'auction',
    'مزادات':               'auction',
    'تحديد الكل':            'select_all',
    'الكل':                 'select_all',
    'توصية دراسات':          'studies_recommendation',
    'توصية الدراسات':        'studies_recommendation',
    'direct_sale':          'direct_sale',
    'auction':              'auction',
    'select_all':           'select_all',
    'studies_recommendation':'studies_recommendation',
}

CUSTOMER_ROLE_MAP = {
    'مالك':   'owner',
    'وكيل':   'agent',
    'وسيط':   'broker',
    'اخر':   'other',
    'آخر':   'other',
    'أخرى':  'other',
    'اخري':  'other',
    'مكتب':  'broker',
    'مسوق':  'broker',
    'owner':  'owner',
    'agent':  'agent',
    'broker': 'broker',
    'other':  'other',
}

PROPERTY_USAGE_MAP = {
    'تجاري وسكني':          'mixed_use',
    'سكني وتجاري':          'mixed_use',
    'تجاري/سكني':          'mixed_use',
    'سكني/تجاري':          'mixed_use',
    'مختلط':               'mixed_use',
    'تجاري':               'commercial',
    'سكني':                'residential',
    'عماير سكنية':          'residential_buildings',
    'عمائر سكنية':          'residential_buildings',
    'مباني سكنية':          'residential_buildings',
    'صناعي':               'industrial',
    'مستودعات وتخزين':     'warehouses_storage',
    'مستودعات':             'warehouses_storage',
    'تخزين':               'warehouses_storage',
    'خدمات ومرافق':         'services_public',
    'خدمات':               'services_public',
    'مرافق عامة':           'services_public',
    'ترفيهي وسياحي':        'recreation_tourism',
    'ترفيهي':               'recreation_tourism',
    'سياحي':               'recreation_tourism',
    'إيواء سياحي':          'tourist_lodging',
    'ايواء سياحي':          'tourist_lodging',
    'فندقي':               'tourist_lodging',
    'شقق مخدومة':           'tourist_lodging',
    'مواقف سيارات':         'parking_lots',
    'مواقف':               'parking_lots',
    'زراعي':               'agricultural',
    'mixed_use':           'mixed_use',
    'commercial':          'commercial',
    'residential':         'residential',
    'residential_buildings':'residential_buildings',
    'industrial':          'industrial',
    'warehouses_storage':  'warehouses_storage',
    'services_public':     'services_public',
    'recreation_tourism':  'recreation_tourism',
    'tourist_lodging':     'tourist_lodging',
    'parking_lots':        'parking_lots',
    'agricultural':        'agricultural',
    'Agricultural':        'agricultural',
    'agriculture':         'agricultural',
    'Agriculture':         'agricultural',
}

REQUIRES_OFFER_MAP = {
    'نعم': 'yes',
    'لا':  'no',
    'yes': 'yes',
    'no':  'no',
}

OWNER_TYPE_MAP = {
    'فرد':        'individual',
    'شركة':       'company',
    'جهة حكومية': 'government',
    'مستثمر':     'investor',
    'individual': 'individual',
    'company':    'company',
    'government': 'government',
    'investor':   'investor',
}

HAS_INCOME_MAP = {
    'نعم': 'yes',
    'لا':  'no',
    'yes': 'yes',
    'no':  'no',
}


class EntriesImportWizard(models.TransientModel):
    _name = 'entries.import.wizard'
    _description = 'Import Entries from Excel'

    file_data = fields.Binary(
        string='Excel File',
        required=False,
        attachment=False,
    )
    file_name = fields.Char(string='File Name')

    @api.model
    def _get_default_template_file(self):
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'static',
            'data',
            'entries_import_template.xlsx'
        )
        content = False
        if os.path.exists(template_path):
            try:
                with open(template_path, 'rb') as f:
                    content = base64.b64encode(f.read())
            except Exception as e:
                _logger.warning("Failed to read template file at %s: %s", template_path, e)

        if not content:
            try:
                import openpyxl
                from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
                from openpyxl.utils import get_column_letter

                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = 'قالب الاستيراد'
                ws.views.sheetView[0].rightToLeft = True
                headers = [
                    'رغبة العميل', 'اسم العميل', 'صفة العميل', 'نوع المالك', 'رقم التواصل مع العميل',
                    'هل يتطلب عرض فني؟', 'اسم المدرج', 'ايميل المدرج', 'نوع العقار', 'استخدام العقار',
                    'المساحة (م²)', 'سعر العميل (للمتر مربع)', 'هل يوجد دخل؟', 'الدخل الحالي',
                    'المدينة', 'الحي', 'الموقع (اللوكيشن)', 'رقم القطعة',
                    'رقم الصك', 'تاريخ الصك', 'رقم المخطط', 'تاريخ الإدراج', 'ملاحظات'
                ]
                sample_row = [
                    'بيع مباشر', 'أسس العقار', 'مالك', 'فرد', '0501234567',
                    'نعم', 'Administrator', 'admin@example.com', 'أرض تجارية سكنية', 'سكني',
                    500.00, 345.00, 'نعم', 0.00,
                    'الرياض', 'حي الربوة', 'https://maps.google.com/?q=24.7,46.6', '543',
                    '123456789', '1445-05-20', '1020', '2026-10-04', 'ملاحظات تجريبية'
                ]
                ws.append(headers)
                ws.append(sample_row)

                header_fill = PatternFill(start_color='1B4375', end_color='1B4375', fill_type='solid')
                header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
                header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                white_side = Side(style='thin', color='FFFFFF')
                header_border = Border(left=white_side, right=white_side, top=white_side, bottom=white_side)
                ws.row_dimensions[1].height = 30

                for col_idx, col in enumerate(ws.iter_cols(min_row=1, max_row=1), 1):
                    cell = col[0]
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = header_alignment
                    cell.border = header_border
                    max_len = max(len(str(c.value or '')) for c in ws[get_column_letter(col_idx)])
                    ws.column_dimensions[get_column_letter(col_idx)].width = max(max_len + 5, 18)

                for r in ws.iter_rows(min_row=2):
                    for cell in r:
                        cell.alignment = Alignment(horizontal='center', vertical='center')

                out = io.BytesIO()
                wb.save(out)
                content = base64.b64encode(out.getvalue())
            except Exception as ex:
                _logger.error("Failed to generate fallback template: %s", ex)

        return content

    template_file = fields.Binary(
        string='Import Template',
        default=_get_default_template_file,
        readonly=True,
    )
    template_filename = fields.Char(
        string='Import Template Name',
        default='entries_import_template.xlsx',
    )

    result_info = fields.Text(string='Import Result', readonly=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Done')],
        default='draft',
    )

    def action_download_template(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/sales_and_auction_management/static/data/entries_import_template.xlsx',
            'target': 'self',
        }

    def _get_column_field_name(self, header):
        if not header:
            return False
        header_str = str(header).strip()
        if header_str in COLUMN_MAP:
            return COLUMN_MAP[header_str]

        normalized = re.sub(r'\s+', ' ', header_str).strip()
        if normalized in COLUMN_MAP:
            return COLUMN_MAP[normalized]

        clean_punct = re.sub(r'[\(\)\?\؟]', '', normalized).strip()
        clean_punct = re.sub(r'\s+', ' ', clean_punct).strip()
        if clean_punct in COLUMN_MAP:
            return COLUMN_MAP[clean_punct]

        return False

    def action_import(self):
        """Read the uploaded Excel file and create entries records."""
        self.ensure_one()
        if not self.file_data:
            raise UserError(_("Please upload an Excel file first."))

        try:
            import openpyxl
        except ImportError:
            raise UserError(_("The openpyxl library is not available. Please contact the system administrator."))

        try:
            raw = base64.b64decode(self.file_data)
            wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
        except Exception as e:
            raise UserError(_("Could not read the file: %s") % str(e))

        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise UserError(_("The file is empty."))

        header_row = [str(h).strip() if h else '' for h in rows[0]]
        mapped_headers = [self._get_column_field_name(h) for h in header_row]
        if not any(mapped_headers):
            raise UserError(
                _("File columns were not recognized. "
                  "Please use the provided template or ensure column headers match.")
            )

        error_lines = []
        all_row_vals = []

        for row_idx, row in enumerate(rows[1:], start=2):
            if all(cell is None or str(cell).strip() == '' for cell in row):
                continue

            row_vals = {}
            for col_idx, field_name in enumerate(mapped_headers):
                if not field_name:
                    continue
                cell_val = row[col_idx] if col_idx < len(row) else None
                if cell_val is None or str(cell_val).strip() == '':
                    continue
                row_vals[field_name] = cell_val

            all_row_vals.append({'row_idx': row_idx, 'data': row_vals})

        if error_lines:
            summary_parts = [_("\n⚠️ Errors found in the file (%d lines):") % len(error_lines)]
            summary_parts.extend(error_lines)
            self.write({
                'result_info': "\n".join(summary_parts),
                'state': 'done',
            })
            return self._reopen()

        return self._do_import(all_row_vals)

    def _do_import(self, all_row_vals):
        created_count = 0
        error_lines = []
        all_vals = []

        try:
            with self.env.cr.savepoint():
                for item in all_row_vals:
                    row_idx = item['row_idx']
                    row_data = item['data']
                    try:
                        vals = self._build_entry_vals(row_data)
                        all_vals.append(vals)
                    except Exception as e:
                        error_lines.append(_("Line %d: %s") % (row_idx, str(e)))
                        _logger.warning("[EntriesImport] Row %d error: %s", row_idx, str(e))

                if error_lines:
                    raise UserError(_("Validation failed"))

                if all_vals:
                    self.env['entries'].create(all_vals)
                    created_count = len(all_vals)

        except UserError:
            pass
        except Exception as e:
            error_lines.append(_("Unexpected error: %s") % str(e))
            _logger.exception("Import Wizard Error")

        if error_lines:
            summary_parts = [_("\n⚠️ Errors found in the file (%d lines):") % len(error_lines)]
            summary_parts.extend(error_lines)
            summary_parts.append(_("\nNo records were created. Please fix the errors and try again."))
            self.write({
                'result_info': "\n".join(summary_parts),
                'state': 'done',
            })
        else:
            self.write({
                'result_info': _("✅ %d entries created successfully.") % created_count,
                'state': 'done',
            })

        return self._reopen()

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'entries.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _validate_saudi_mobile(self, phone):
        if not phone:
            return False

        phone_str = str(phone).strip().replace(' ', '')
        if phone_str.endswith('.0'):
            phone_str = phone_str[:-2]
        if not phone_str:
            return False

        normalized = phone_str
        if phone_str.startswith('+966'):
            normalized = phone_str[4:]
        elif phone_str.startswith('00966'):
            normalized = phone_str[5:]
        elif phone_str.startswith('966'):
            normalized = phone_str[3:]
        elif phone_str.startswith('05'):
            normalized = phone_str[1:]
        elif phone_str.startswith('5') and len(phone_str) == 9:
            normalized = phone_str

        if not normalized.isdigit() or not normalized.startswith('5') or len(normalized) != 9:
            raise UserError(_("The phone number '%s' must be a valid Saudi mobile (e.g., 05xxxxxxxx, +9665xxxxxxxx, or 009665xxxxxxxx).") % phone_str)

        return normalized

    def _build_entry_vals(self, row_vals):
        vals = {}

        # ── Mobile Number Validation ───────────────────────────────────
        if 'partner_mobile' in row_vals:
            cleaned_phone = self._validate_saudi_mobile(row_vals['partner_mobile'])
            if cleaned_phone:
                vals['partner_mobile'] = cleaned_phone
                row_vals['partner_mobile'] = cleaned_phone

        # ── Many2one / Relational fields ───────────────────────────────
        if 'customer_intent_rel' in row_vals or 'customer_intent' in row_vals:
            raw_val = str(row_vals.get('customer_intent_rel') or row_vals.get('customer_intent')).strip()
            key = CUSTOMER_INTENT_MAP.get(raw_val) or raw_val
            intent_rec = self.env['customer.intent'].search(['|', ('code', '=', key), ('name', '=', raw_val)], limit=1)
            if not intent_rec:
                intent_rec = self.env['customer.intent'].search(['|', ('code', '=ilike', key), ('name', '=ilike', raw_val)], limit=1)
            if not intent_rec:
                intent_rec = self.env['customer.intent'].search(['|', ('name', 'ilike', raw_val), ('code', 'ilike', raw_val)], limit=1)
            if not intent_rec:
                raise UserError(
                    _("Customer Intent '%s' not found in database.") % raw_val
                )
            vals['customer_intent_rel'] = intent_rec.id
            if intent_rec.code:
                vals['customer_intent'] = intent_rec.code

        if 'customer_role_rel' in row_vals or 'customer_role' in row_vals:
            raw_val = str(row_vals.get('customer_role_rel') or row_vals.get('customer_role')).strip()
            key = CUSTOMER_ROLE_MAP.get(raw_val) or raw_val
            role_rec = self.env['customer.role'].search(['|', ('code', '=', key), ('name', '=', raw_val)], limit=1)
            if not role_rec:
                role_rec = self.env['customer.role'].search(['|', ('code', '=ilike', key), ('name', '=ilike', raw_val)], limit=1)
            if not role_rec:
                role_rec = self.env['customer.role'].search(['|', ('name', 'ilike', raw_val), ('code', 'ilike', raw_val)], limit=1)
            if not role_rec:
                raise UserError(
                    _("Customer Role '%s' not found in database.") % raw_val
                )
            vals['customer_role_rel'] = role_rec.id

        if 'property_usage_rel' in row_vals or 'property_usage' in row_vals:
            raw_val = str(row_vals.get('property_usage_rel') or row_vals.get('property_usage')).strip()
            key = PROPERTY_USAGE_MAP.get(raw_val) or PROPERTY_USAGE_MAP.get(raw_val.lower()) or raw_val
            usage_rec = self.env['property.usage.type'].search(['|', ('code', '=', key), ('name', '=', raw_val)], limit=1)
            if not usage_rec:
                usage_rec = self.env['property.usage.type'].search(['|', ('code', '=ilike', key), ('name', '=ilike', raw_val)], limit=1)
            if not usage_rec:
                usage_rec = self.env['property.usage.type'].search(['|', ('name', 'ilike', raw_val), ('code', 'ilike', raw_val)], limit=1)
            if not usage_rec and key == 'agricultural':
                usage_rec = self.env.ref('bussma_system.property_usage_agricultural', raise_if_not_found=False)
            if not usage_rec:
                raise UserError(
                    _("Property Usage '%s' not found in database.") % raw_val
                )
            vals['property_usage_rel'] = usage_rec.id

        if 'owner_type' in row_vals:
            val_str = str(row_vals['owner_type']).strip()
            key = OWNER_TYPE_MAP.get(val_str)
            if not key:
                if 'فرد' in val_str: key = 'individual'
                elif 'شركة' in val_str: key = 'company'
                elif 'جهة' in val_str or 'حكوم' in val_str: key = 'government'
                elif 'مستثمر' in val_str: key = 'investor'
            if not key:
                raise UserError(
                    _("Invalid value for 'Owner Type': %s. Supported values: فرد, شركة, جهة حكومية, مستثمر.") % row_vals['owner_type']
                )
            vals['owner_type'] = key

        if 'has_income' in row_vals:
            val_str = str(row_vals['has_income']).strip()
            key = HAS_INCOME_MAP.get(val_str)
            if not key:
                if 'نعم' in val_str or 'yes' in val_str.lower() or 'true' in val_str.lower(): key = 'yes'
                elif 'لا' in val_str or 'no' in val_str.lower() or 'false' in val_str.lower(): key = 'no'
            if not key:
                raise UserError(
                    _("Invalid value for 'Has Income': %s. Supported values: نعم, لا.") % row_vals['has_income']
                )
            vals['has_income'] = key

        if 'requires_technical_offer' in row_vals:
            val_str = str(row_vals['requires_technical_offer']).strip()
            key = REQUIRES_OFFER_MAP.get(val_str)
            if not key:
                if 'نعم' in val_str or 'yes' in val_str.lower() or 'true' in val_str.lower(): key = 'yes'
                elif 'لا' in val_str or 'no' in val_str.lower() or 'false' in val_str.lower(): key = 'no'
            if not key:
                raise UserError(
                    _("Invalid value for 'Requires Technical Offer': %s") % row_vals['requires_technical_offer']
                )
            vals['requires_technical_offer'] = key

        # ── Many2one: res.partner (Customer Name) ───────────────────────
        if 'partner_id' in row_vals:
            name = str(row_vals['partner_id']).strip()
            partner = self.env['res.partner'].search(
                [('name', '=', name), ('is_customer', '=', True)], limit=1
            )
            if not partner:
                partner = self.env['res.partner'].search(
                    [('name', 'ilike', name), ('is_customer', '=', True)], limit=1
                )

            if not partner:
                partner_vals = {
                    'name': name,
                    'is_customer': True,
                    'mobile': row_vals.get('partner_mobile'),
                }
                partner = self.env['res.partner'].create(partner_vals)
                _logger.info("[EntriesImport] Created new customer: %s", name)
            elif 'partner_mobile' in row_vals and not partner.mobile:
                partner.write({'mobile': row_vals['partner_mobile']})

            vals['partner_id'] = partner.id

        # ── Many2one: res.users (Entered By) & Entered By Email ─────────
        entered_user = False
        user_by_email = False
        if 'entered_by_email' in row_vals:
            email_val = str(row_vals['entered_by_email']).strip()
            if email_val:
                vals['entered_by_email'] = email_val
                user_by_email = self.env['res.users'].search([('email', '=ilike', email_val)], limit=1)
                if not user_by_email:
                    user_by_email = self.env['res.users'].search([('login', '=ilike', email_val)], limit=1)
                entered_user = user_by_email

        if not entered_user and 'entered_by_name' in row_vals:
            name_val = str(row_vals['entered_by_name']).strip()
            if name_val:
                entered_user = self.env['res.users'].search([('name', '=ilike', name_val)], limit=1)

        if entered_user:
            vals['entered_by_id'] = entered_user.id
            if entered_user.email and not vals.get('entered_by_email'):
                vals['entered_by_email'] = entered_user.email
        else:
            vals['entered_by_id'] = self.env.user.id
            if self.env.user.email and not vals.get('entered_by_email'):
                vals['entered_by_email'] = self.env.user.email

        # ── Many2one: res.users (Assigned Negotiator) strictly based on entered_by_email ──
        if user_by_email:
            vals['assigned_negotiator'] = user_by_email.id

        # ── Many2one: property.type ──────────────────────────────────────
        if 'property_type' in row_vals:
            ptype_name = str(row_vals['property_type']).strip()
            ptype = self.env['property.type'].search([('name', '=', ptype_name)], limit=1)
            if not ptype:
                ptype = self.env['property.type'].search([('name', 'ilike', ptype_name)], limit=1)

            if not ptype:
                raise UserError(_("Property Type not found: '%s'.") % ptype_name)

            vals['property_type'] = ptype.id

        # ── Many2one: res.country.state (City) ──────────────────────────
        if 'city' in row_vals:
            city_name = str(row_vals['city']).strip()
            city = self.env['res.country.state'].search([
                ('name', '=', city_name),
                ('country_id.code', '=', 'SA'),
                ('code', 'ilike', 'CT_'),
            ], limit=1)
            if not city:
                city = self.env['res.country.state'].search([
                    ('name', 'ilike', city_name),
                    ('country_id.code', '=', 'SA'),
                    ('code', 'ilike', 'CT_'),
                ], limit=1)
            if not city:
                raise UserError(_("City not found: '%s'.") % city_name)
            vals['city'] = city.id

        # ── Many2one: res.city (District) - Auto create if missing ──────
        if 'district_id' in row_vals:
            dist_name = str(row_vals['district_id']).strip()
            city_id = vals.get('city')
            domain = [('name', '=', dist_name)]
            if city_id:
                domain.append(('state_id', '=', city_id))
            district = self.env['res.city'].search(domain, limit=1)
            if not district and city_id:
                district = self.env['res.city'].search(
                    [('name', 'ilike', dist_name), ('state_id', '=', city_id)], limit=1
                )
            if not district:
                district = self.env['res.city'].search(
                    [('name', 'ilike', dist_name)], limit=1
                )
            if not district:
                # Auto create district and link to city
                district_vals = {'name': dist_name}
                if city_id:
                    district_vals['state_id'] = city_id
                district = self.env['res.city'].create(district_vals)
                _logger.info("[EntriesImport] Created new district '%s' linked to state_id %s", dist_name, city_id)
            vals['district_id'] = district.id

        # ── Numeric fields ───────────────────────────────────────────────
        for field in ('area_sqm', 'customer_price_per_sqm', 'current_income'):
            if field in row_vals:
                try:
                    vals[field] = float(row_vals[field])
                except (ValueError, TypeError):
                    raise UserError(
                        _("Invalid numerical value in field '%s': %s") % (field, row_vals[field])
                    )

        # ── Auto set has_income if current_income is provided ────────────
        if vals.get('current_income') and not vals.get('has_income'):
            vals['has_income'] = 'yes'

        # ── Date fields (deed_date, deed_date_hijri, listing_date) ───────
        if 'deed_date' in row_vals:
            g_date, h_str = parse_date_value(row_vals['deed_date'])
            if g_date:
                vals['deed_date'] = g_date
            if h_str and 'deed_date_hijri' in self.env['entries']._fields and 'deed_date_hijri' not in vals:
                vals['deed_date_hijri'] = h_str

        if 'deed_date_hijri' in row_vals:
            g_date, h_str = parse_date_value(row_vals['deed_date_hijri'])
            if g_date and 'deed_date' not in vals:
                vals['deed_date'] = g_date
            if h_str and 'deed_date_hijri' in self.env['entries']._fields and 'deed_date_hijri' not in vals:
                vals['deed_date_hijri'] = h_str

        if 'listing_date' in row_vals:
            g_date, h_str = parse_date_value(row_vals['listing_date'])
            if g_date:
                vals['listing_date'] = g_date

        # ── Char / Text fields ───────────────────────────────────────────
        for field in ('location_url', 'plot_number', 'plan_number', 'deed_number', 'entered_notes', 'partner_mobile'):
            if field in row_vals and field not in vals:
                vals[field] = str(row_vals[field]).strip()

        return vals
