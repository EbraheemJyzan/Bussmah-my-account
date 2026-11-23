# -*- coding: utf-8 -*-
import base64
import io
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
#  Column header mapping for Eanfaz Properties                                #
# --------------------------------------------------------------------------- #
EANFAZ_COLUMN_MAP = {
    # Government Auction Info
    'فئة المزاد': 'auction_category',
    'هل يحتاج إلى هوية؟': 'need_identity',
    'هل يحتاج إلى هوية': 'need_identity',
    'يحتاج إلى هوية': 'need_identity',
    'auction_category': 'auction_category',
    'need_identity': 'need_identity',

    # Execution Applicant Info
    'رقم الأصل': 'asset_number',
    'رقم القرار القضائي': 'court_decision_number',
    'اسم طالب التنفيذ': 'execution_applicant_name',
    'رقم تواصل طالب التنفيذ': 'execution_applicant_phone',
    'asset_number': 'asset_number',
    'court_decision_number': 'court_decision_number',
    'execution_applicant_name': 'execution_applicant_name',
    'execution_applicant_phone': 'execution_applicant_phone',

    # Deed Info
    'رقم الصك': 'deed_number',
    'تاريخ الصك': 'deed_date',
    'تاريخ الصك (هجري)': 'deed_date_hijri',
    'تاريخ الصك هجري': 'deed_date_hijri',
    'جهة إصدار الصك': 'deed_issuer',
    'رقم المخطط': 'plan_number',
    'رقم القطعة': 'plot_number',
    'deed_number': 'deed_number',
    'deed_date': 'deed_date',
    'deed_date_hijri': 'deed_date_hijri',
    'deed_issuer': 'deed_issuer',
    'plan_number': 'plan_number',
    'plot_number': 'plot_number',

    # Location & Area Info
    'المدينة': 'city',
    'المدينه': 'city',
    'الحي': 'district_id',
    'نوع العقار': 'property_type',
    'المساحة': 'area_sqm',
    'المساحه': 'area_sqm',
    'المساحة (م²)': 'area_sqm',
    'المساحة (م2)': 'area_sqm',
    'الموقع': 'location_url',
    'city': 'city',
    'district_id': 'district_id',
    'property_type': 'property_type',
    'area_sqm': 'area_sqm',
    'location_url': 'location_url',

    # Dimensions & Borders (North / South)
    'الحد (شمال)': 'limit_north',
    'الحد شمال': 'limit_north',
    'الطول (شمال)': 'length_north',
    'طول شمال': 'length_north',
    'الحد (جنوب)': 'limit_south',
    'الحد جنوب': 'limit_south',
    'الطول (جنوب)': 'length_south',
    'طول جنوب': 'length_south',
    'limit_north': 'limit_north',
    'length_north': 'length_north',
    'limit_south': 'limit_south',
    'length_south': 'length_south',

    # Dimensions & Borders (East / West)
    'الحد (شرق)': 'limit_east',
    'الحد شرق': 'limit_east',
    'الطول (شرق)': 'length_east',
    'طول شرق': 'length_east',
    'الحد (غرب)': 'limit_west',
    'الحد غرب': 'limit_west',
    'الطول (غرب)': 'length_west',
    'طول غرب': 'length_west',
    'limit_east': 'limit_east',
    'length_east': 'length_east',
    'limit_west': 'limit_west',
    'length_west': 'length_west',

    # Description, Notes & Operation Info
    'وصف العقار': 'property_description',
    'رابط صور العقار': 'property_images_url',
    'ملاحظات المشروع': 'project_notes',
    'نوع عقد التأجير': 'lease_contract_type',
    'هل يوجد عقد تشغيل؟': 'has_operation_contract',
    'هل يوجد عقد تشغيل': 'has_operation_contract',
    'تاريخ انتهاء عقود التأجير': 'lease_contract_expiry_date',
    'ملاحظات مدير المشروع': 'project_manager_notes',
    'property_description': 'property_description',
    'property_images_url': 'property_images_url',
    'project_notes': 'project_notes',
    'lease_contract_type': 'lease_contract_type',
    'has_operation_contract': 'has_operation_contract',
    'lease_contract_expiry_date': 'lease_contract_expiry_date',
    'project_manager_notes': 'project_manager_notes',
}

AUCTION_CATEGORY_MAP = {
    'VIP': 'vip',
    'vip': 'vip',
    'أ': 'a',
    'ا': 'a',
    'A': 'a',
    'a': 'a',
    'ب': 'b',
    'B': 'b',
    'b': 'b',
    'ج': 'c',
    'C': 'c',
    'c': 'c',
}

NEED_IDENTITY_MAP = {
    'نعم': 'yes',
    'لا': 'no',
    'yes': 'yes',
    'no': 'no',
}

LEASE_CONTRACT_TYPE_MAP = {
    'إلكتروني': 'electronic',
    'الكتروني': 'electronic',
    'عادي': 'normal',
    'غير محدد': 'not_applicable',
    'غير مطبق': 'not_applicable',
    'لا يوجد': 'not_applicable',
    'electronic': 'electronic',
    'normal': 'normal',
    'not_applicable': 'not_applicable',
}

HAS_OPERATION_CONTRACT_MAP = {
    'نعم': True,
    'لا': False,
    'yes': True,
    'no': False,
    'true': True,
    'false': False,
}


class EanfazEntriesImportWizard(models.TransientModel):
    _name = 'eanfaz.entries.import.wizard'
    _description = 'Import Eanfaz Properties from Excel'

    @api.model
    def _get_default_template_file(self):
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'static',
            'data',
            'eanfaz_entries_import_template.xlsx'
        )
        content = False
        if os.path.exists(template_path):
            try:
                with open(template_path, 'rb') as f:
                    content = base64.b64encode(f.read())
            except Exception as e:
                _logger.warning("Failed to read Eanfaz template file at %s: %s", template_path, e)

        if not content:
            try:
                import openpyxl
                from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
                from openpyxl.utils import get_column_letter

                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = 'Eanfaz Properties Template'
                ws.views.sheetView[0].rightToLeft = True
                headers = [
                    'فئة المزاد', 'هل يحتاج إلى هوية؟',
                    'رقم الأصل', 'رقم القرار القضائي', 'اسم طالب التنفيذ', 'رقم تواصل طالب التنفيذ',
                    'رقم الصك', 'تاريخ الصك', 'جهة إصدار الصك', 'رقم المخطط', 'رقم القطعة',
                    'المدينة', 'الحي', 'نوع العقار', 'المساحة (م²)', 'الموقع',
                    'الحد (شمال)', 'الطول (شمال)', 'الحد (جنوب)', 'الطول (جنوب)',
                    'الحد (شرق)', 'الطول (شرق)', 'الحد (غرب)', 'الطول (غرب)',
                    'وصف العقار', 'رابط صور العقار', 'ملاحظات المشروع',
                    'نوع عقد التأجير', 'هل يوجد عقد تشغيل؟', 'تاريخ انتهاء عقود التأجير', 'ملاحظات مدير المشروع'
                ]
                sample_row = [
                    'VIP', 'نعم',
                    '8968', '666', 'عبدالله أحمد', '0566666666',
                    '123456789', '1445-05-20', 'كتابة العدل بالرياض', '1020', '55',
                    'الرياض', 'حي النرجس', 'أرض سكنية', 500.00, 'https://maps.google.com/?q=24.7,46.6',
                    'شارع عرض 15م', 20.00, 'قطعة رقم 56', 20.00,
                    'قطعة رقم 54', 25.00, 'شارع عرض 20م', 25.00,
                    'عقار سكني بموقع متميز مع كافة الخدمات', 'https://images.example.com/property1', 'جاهز للمزاد',
                    'إلكتروني', 'نعم', '2026-10-26', 'مكتمل المستندات'
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
                _logger.error("Failed to generate fallback template for Eanfaz: %s", ex)

        return content

    file_data = fields.Binary(
        string='Excel File',
        required=False,
        attachment=False,
    )
    file_name = fields.Char(string='File Name')
    template_file = fields.Binary(
        string='Import Template',
        default=_get_default_template_file,
        readonly=True,
    )
    template_filename = fields.Char(
        string='Import Template Name',
        default='eanfaz_entries_import_template.xlsx',
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
            'url': '/sales_and_auction_management/static/data/eanfaz_entries_import_template.xlsx',
            'target': 'self',
        }

    def _get_column_field_name(self, header):
        if not header:
            return False
        header_str = str(header).strip()
        if header_str in EANFAZ_COLUMN_MAP:
            return EANFAZ_COLUMN_MAP[header_str]

        normalized = re.sub(r'\s+', ' ', header_str).strip()
        if normalized in EANFAZ_COLUMN_MAP:
            return EANFAZ_COLUMN_MAP[normalized]

        clean_punct = re.sub(r'[\(\)\?\؟]', '', normalized).strip()
        clean_punct = re.sub(r'\s+', ' ', clean_punct).strip()
        if clean_punct in EANFAZ_COLUMN_MAP:
            return EANFAZ_COLUMN_MAP[clean_punct]

        return False

    def action_import(self):
        """Read the uploaded Excel file and create Eanfaz properties in sales.auction.management."""
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
            raise UserError(_("The uploaded file is empty."))

        header_row = [str(h).strip() if h else '' for h in rows[0]]
        mapped_headers = [self._get_column_field_name(h) for h in header_row]
        if not any(mapped_headers):
            raise UserError(_("File columns were not recognized. Please use the provided template or ensure column headers match."))

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

        return self._do_import(all_row_vals)

    def _do_import(self, all_row_vals):
        created_count = 0
        error_lines = []
        all_vals = []

        request_type = self.env.ref('sales_and_auction_management.p2_type_auction_enf', raise_if_not_found=False)
        stage = self.env.ref('sales_and_auction_management.p2_auction_enf_portfolio', raise_if_not_found=False)
        project = self.env.ref('sales_and_auction_management.project_auctions_enf_basic', raise_if_not_found=False)

        try:
            with self.env.cr.savepoint():
                for item in all_row_vals:
                    row_idx = item['row_idx']
                    row_data = item['data']
                    try:
                        vals = self._build_eanfaz_vals(row_data)
                        if request_type:
                            vals['request_type_id'] = request_type.id
                        if stage:
                            vals['stage_id'] = stage.id
                        if project:
                            vals['project_id'] = project.id
                        vals['auction_project_path'] = 'enforcement'

                        all_vals.append(vals)
                    except Exception as e:
                        error_lines.append(_("Line %d: %s") % (row_idx, str(e)))
                        _logger.warning("[EanfazImport] Row %d error: %s", row_idx, str(e))

                if error_lines:
                    raise UserError(_("Data validation failed."))

                if all_vals:
                    records = self.env['sales.auction.management'].create(all_vals)
                    created_count = len(records)

        except UserError:
            pass
        except Exception as e:
            error_lines.append(_("Unexpected error: %s") % str(e))
            _logger.exception("Eanfaz Import Wizard Error")

        if error_lines:
            summary_parts = [_("\n⚠️ Errors found in the file (%d lines):") % len(error_lines)]
            summary_parts.extend(error_lines)
            summary_parts.append(_("\nNo properties were created. Please fix the errors and try again."))
            self.write({
                'result_info': "\n".join(summary_parts),
                'state': 'done',
            })
        else:
            self.write({
                'result_info': _("✅ %d Eanfaz properties created successfully.") % created_count,
                'state': 'done',
            })

        return self._reopen()

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'eanfaz.entries.import.wizard',
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

    def _build_eanfaz_vals(self, row_vals):
        vals = {}
        vals['auction_project_path'] = 'enforcement'

        # 1. Selection fields
        if 'auction_category' in row_vals:
            val_str = str(row_vals['auction_category']).strip()
            key = AUCTION_CATEGORY_MAP.get(val_str)
            if not key:
                raise UserError(_("Invalid value for 'Auction Category': '%s'. Supported values: VIP, A, B, C.") % val_str)
            vals['auction_category'] = key

        if 'need_identity' in row_vals:
            val_str = str(row_vals['need_identity']).strip()
            key = NEED_IDENTITY_MAP.get(val_str)
            if not key:
                raise UserError(_("Invalid value for 'Need Identity': '%s'. Supported values: Yes, No.") % val_str)
            vals['need_identity'] = key

        if 'lease_contract_type' in row_vals:
            val_str = str(row_vals['lease_contract_type']).strip()
            key = LEASE_CONTRACT_TYPE_MAP.get(val_str)
            if not key:
                raise UserError(_("Invalid value for 'Lease Contract Type': '%s'. Supported values: Electronic, Normal, Not Applicable.") % val_str)
            vals['lease_contract_type'] = key

        if 'has_operation_contract' in row_vals:
            val_str = str(row_vals['has_operation_contract']).strip()
            val_bool = HAS_OPERATION_CONTRACT_MAP.get(val_str)
            if val_bool is None:
                raise UserError(_("Invalid value for 'Has Operation Contract': '%s'. Supported values: Yes, No.") % val_str)
            vals['has_operation_contract'] = val_bool

        # 2. Applicant Phone Validation
        if 'execution_applicant_phone' in row_vals:
            cleaned_phone = self._validate_saudi_mobile(row_vals['execution_applicant_phone'])
            if cleaned_phone:
                vals['execution_applicant_phone'] = cleaned_phone

        # 3. Many2one fields: city, district_id, property_type
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
                district = self.env['res.city'].search([('name', 'ilike', dist_name)], limit=1)
            if not district:
                # Auto create district and link to city
                district_vals = {'name': dist_name}
                if city_id:
                    district_vals['state_id'] = city_id
                district = self.env['res.city'].create(district_vals)
                _logger.info("[EanfazImport] Created new district '%s' linked to state_id %s", dist_name, city_id)
            vals['district_id'] = district.id

        if 'property_type' in row_vals:
            ptype_name = str(row_vals['property_type']).strip()
            ptype = self.env['property.type'].search([('name', '=', ptype_name)], limit=1)
            if not ptype:
                ptype = self.env['property.type'].search([('name', 'ilike', ptype_name)], limit=1)
            if not ptype:
                raise UserError(_("Property Type not found: '%s'.") % ptype_name)
            vals['property_type'] = ptype.id

        # 4. Numeric fields
        num_fields = ('area_sqm', 'length_north', 'length_south', 'length_east', 'length_west')
        for field in num_fields:
            if field in row_vals:
                try:
                    vals[field] = float(row_vals[field])
                except (ValueError, TypeError):
                    raise UserError(_("Invalid numerical value in field '%s': %s") % (field, row_vals[field]))

        # 5. Date fields (deed_date, deed_date_hijri, lease_contract_expiry_date)
        if 'deed_date' in row_vals:
            g_date, h_str = parse_date_value(row_vals['deed_date'])
            if g_date:
                vals['deed_date'] = g_date
            if h_str and 'deed_date_hijri' not in vals:
                vals['deed_date_hijri'] = h_str

        if 'deed_date_hijri' in row_vals:
            g_date, h_str = parse_date_value(row_vals['deed_date_hijri'])
            if g_date and 'deed_date' not in vals:
                vals['deed_date'] = g_date
            if h_str and 'deed_date_hijri' not in vals:
                vals['deed_date_hijri'] = h_str

        if 'lease_contract_expiry_date' in row_vals:
            g_date, h_str = parse_date_value(row_vals['lease_contract_expiry_date'])
            if g_date:
                vals['lease_contract_expiry_date'] = g_date

        # 6. Char and Text fields
        char_fields = (
            'asset_number', 'court_decision_number', 'execution_applicant_name',
            'deed_number', 'deed_date_hijri', 'deed_issuer', 'plan_number', 'plot_number',
            'location_url', 'limit_north', 'limit_south', 'limit_east', 'limit_west',
            'property_description', 'property_images_url', 'project_notes', 'project_manager_notes'
        )
        for field in char_fields:
            if field in row_vals and field not in vals:
                vals[field] = str(row_vals[field]).strip()

        return vals
