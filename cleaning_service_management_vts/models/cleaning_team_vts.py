from odoo import models, fields

class CleaningTeam(models.Model):
    _name = 'cleaning.team.vts'
    _description = 'Cleaning Team'

    name = fields.Char(string="Team Name", required=True)

    leader_id = fields.Many2one(
        'res.users',
        string="Team Leader"
    )

    employee_ids = fields.Many2many(
        'hr.employee',
        string="Team Members"
    )

    cleaning_shift_id = fields.Many2one(
        'cleaning.shift.vts',
        string="Shift"
    )

    active = fields.Boolean(default=True)
    note = fields.Text(string="Notes")

    booked_request_ids = fields.One2many('booking.request','cleaning_team_id', string="Booked Request")