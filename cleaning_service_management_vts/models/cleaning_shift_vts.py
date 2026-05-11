# -*- coding: utf-8 *-*
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CleaningShiftVTS(models.Model):
    _name = 'cleaning.shift.vts'
    _description = 'Cleaning Shift'

    name = fields.Char(
        string='Shift Name',
        required=True
    )
    start_time = fields.Float(string='Start Time', help="Start time of the shift")
    end_time = fields.Float(string='End Time', help="Ending time of the shift")
    duration_hours = fields.Float(
        string='Duration (Hours)',
        compute='_compute_duration',
        store=True,
        help="Total duration of the shift in hours."
    )
    note = fields.Text(string='Description', help="Additional details or description about the shift.")

    slot_duration = fields.Selection(
        selection=[
            ('30',  '30 minutes'),
            ('60',  '60 minutes'),
            ('120', '120 minutes'),
            ('180', '180 minutes'),
            ('240', '240 minutes'),
            ('300', '300 minutes'),
            ('360', '360 minutes')
        ],
        string='Slot Duration', default='30'
    )
    slot_interval = fields.Integer(string='Slot Interval (Minutes)', default=30)

    total_slots = fields.Integer(
        string='Total Slots',
        compute='_compute_total_slots',
        store=True,
        help="Total number of time slots available in this shift."
    )

    slot_ids = fields.One2many(
        comodel_name='cleaning.shift.slot.vts',
        inverse_name='shift_id',
        string='Time Slots'
    )

    @api.depends('start_time', 'end_time', 'slot_interval')
    def _compute_total_slots(self):
        for rec in self:
            interval = rec.slot_interval or 0
            duration = abs(rec.end_time - rec.start_time) * 60
            if interval > 0 and duration > 0:
                rec.total_slots = int(duration // interval)
            else:
                rec.total_slots = 0

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            start = rec.start_time or 0.0
            end = rec.end_time or 0.0
            rec.duration_hours = abs(end - start)

    @api.onchange('slot_duration')
    def _onchange_slot_duration(self):
        for rec in self:
            rec.slot_interval = int(rec.slot_duration or 0)

    def _float_to_time_str(self, float_time):
        hours = int(float_time)
        minutes = int(round((float_time - hours) * 60))
        period = 'AM' if hours < 12 else 'PM'
        display_hour = hours % 12 or 12
        return f"{display_hour:02d}:{minutes:02d} {period}"

    def action_generate_slots(self):
        for rec in self:
            interval = rec.slot_interval or 0
            if interval <= 0:
                raise ValidationError("Please set a valid Slot Interval before generating slots.")

            rec.slot_ids.unlink()

            start = rec.start_time
            end = rec.end_time
            interval_in_hours = interval / 60.0

            slots_vals = []
            current = start

            while round(current + interval_in_hours, 6) <= round(end, 6):
                next_time = current + interval_in_hours
                slots_vals.append({
                    'shift_id': rec.id,
                    'name': f"{self._float_to_time_str(current)} to {self._float_to_time_str(next_time)}",
                    'slot_start_time': current,
                    'slot_end_time': next_time,
                })
                current = next_time

            self.env['cleaning.shift.slot.vts'].create(slots_vals)


class CleaningShiftSlotVTS(models.Model):
    _name = 'cleaning.shift.slot.vts'
    _description = 'Cleaning Shift Slot'
    _order = 'slot_start_time'

    shift_id = fields.Many2one(
        comodel_name='cleaning.shift.vts',
        string='Shift',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(string='Slot', readonly=True)
    slot_start_time = fields.Float(string='Start Time', readonly=True)
    slot_end_time = fields.Float(string='End Time', readonly=True)