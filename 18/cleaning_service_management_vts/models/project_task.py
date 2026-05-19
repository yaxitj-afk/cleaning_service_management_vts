# -*- coding: utf-8 *-*
from odoo import models, fields


class ProjectTask(models.Model):
    _inherit = 'project.task'

    booking_id = fields.Many2one(
        'booking.request',
        string="Booking Reference",
        help="Related service booking reference for this task."
    )

    def action_timer_stop(self):
        self.ensure_one()
        timer = self.user_timer_id
        if timer and timer.timer_start and self.display_timesheet_timer:
            minutes = (fields.Datetime.now() - timer.timer_start).total_seconds() / 60.0
            time_spent = minutes / 60.0
            return self._action_open_new_timesheet(time_spent)
        return super().action_timer_stop()