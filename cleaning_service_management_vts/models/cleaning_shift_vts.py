from odoo import models, fields,api


class CleaningShiftVTS(models.Model):
    _name = 'cleaning.shift.vts'
    _description = 'Cleaning Shift'

    name = fields.Char(
        string='Shift Name',
        required=True
    )
    start_time = fields.Float(string='Start Time')
    end_time = fields.Float(string='End Time')
    duration_hours = fields.Float(
        string='Duration (Hours)',
        compute='_compute_duration',
        store=True
    )
    note = fields.Text(string='Description')

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.start_time is not False and rec.end_time is not False:
                rec.duration_hours = rec.end_time - rec.start_time
            else:
                rec.duration_hours = 0.0