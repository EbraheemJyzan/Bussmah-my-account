# -*- coding: utf-8 -*-
import pytz
from datetime import datetime, timedelta
from odoo import models, fields, api

class EntriesStageHistory(models.Model):
    _name = 'entries.stage.history'
    _description = 'Entries Stage History'
    _order = 'start_date desc'

    entry_id = fields.Many2one(
        'entries',
        string='Entry',
        ondelete='cascade',
        required=True
    )
    stage_id = fields.Many2one(
        'request.stage',
        string='Stage',
        required=True,
        domain="[('res_model', '=', 'entries'), ('project_stage_selection', 'not in', ['completed', 'city_study_completed'])]"
    )
    start_date = fields.Datetime(
        string='Start Date',
        default=fields.Datetime.now,
        required=True
    )
    end_date = fields.Datetime(
        string='End Date'
    )
    duration_days = fields.Float(
        string='Duration (Days)',
        compute='_compute_duration',
        store=True,
        digits=(16, 2),
        help='Duration in days excluding weekends (Friday/Saturday) and official holidays from resource.calendar.leaves.'
    )
    is_return = fields.Boolean(
        string='Is Return',
        default=False,
        help='True if this history entry was created due to a return to a previous stage'
    )
    returned_by_user_id = fields.Many2one(
        'res.users',
        string='Returned By',
        help='The user who performed the return'
    )
    is_assign_detailed_study = fields.Boolean(
        string='Assign Detailed Study',
        default=False
    )
    committee_decision = fields.Selection(
        [('direct_sale', 'Direct Sale'), ('auction', 'Auction'), ('exclusion', 'Exclusion')],
        string='Committee Decision'
    )

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        now = fields.Datetime.now()
        tz_name = self.env.user.tz or 'Asia/Riyadh'
        try:
            tz = pytz.timezone(tz_name)
        except Exception:
            tz = pytz.timezone('Asia/Riyadh')

        valid_recs = [rec for rec in self if rec.start_date]
        for rec in self:
            if not rec.start_date:
                rec.duration_days = 0.0

        if not valid_recs:
            return

        min_start = min(rec.start_date for rec in valid_recs)
        max_end = max((rec.end_date or now) for rec in valid_recs)

        leaves = self.env['resource.calendar.leaves'].search([
            ('date_from', '<=', max_end),
            ('date_to', '>=', min_start),
        ])

        holiday_dates = set()
        for l in leaves:
            if not l.date_from or not l.date_to:
                continue
            dt_from = pytz.UTC.localize(l.date_from).astimezone(tz) if not l.date_from.tzinfo else l.date_from.astimezone(tz)
            dt_to = pytz.UTC.localize(l.date_to).astimezone(tz) if not l.date_to.tzinfo else l.date_to.astimezone(tz)
            cur_d = dt_from.date()
            end_d = dt_to.date()
            while cur_d <= end_d:
                holiday_dates.add(cur_d)
                cur_d += timedelta(days=1)

        for rec in valid_recs:
            end = rec.end_date or now
            if end <= rec.start_date:
                rec.duration_days = 0.0
                continue

            start_tz = pytz.UTC.localize(rec.start_date).astimezone(tz) if not rec.start_date.tzinfo else rec.start_date.astimezone(tz)
            end_tz = pytz.UTC.localize(end).astimezone(tz) if not end.tzinfo else end.astimezone(tz)

            total_working_seconds = 0.0
            cur_d = start_tz.date()
            end_d = end_tz.date()

            while cur_d <= end_d:
                # Friday (4) and Saturday (5) are weekend days in Saudi Arabia
                if cur_d.weekday() in (4, 5) or cur_d in holiday_dates:
                    cur_d += timedelta(days=1)
                    continue

                day_start = tz.localize(datetime.combine(cur_d, datetime.min.time()))
                day_next = tz.localize(datetime.combine(cur_d + timedelta(days=1), datetime.min.time()))

                overlap_start = max(start_tz, day_start)
                overlap_end = min(end_tz, day_next)

                if overlap_end > overlap_start:
                    total_working_seconds += (overlap_end - overlap_start).total_seconds()

                cur_d += timedelta(days=1)

            rec.duration_days = round(total_working_seconds / 86400.0, 2)
