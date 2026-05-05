from odoo import models, fields

class BookingDashboard(models.Model):
    _name = 'booking.dashboard'
    _description = 'Booking Dashboard'

    total_requests = fields.Integer(compute="_compute_counts")
    draft_count = fields.Integer(compute="_compute_counts")
    review_count = fields.Integer(compute="_compute_counts")
    approved_count = fields.Integer(compute="_compute_counts")
    rejected_count = fields.Integer(compute="_compute_counts")

    def _compute_counts(self):
        Booking = self.env['booking.request']

        for rec in self:
            rec.total_requests = Booking.search_count([])
            rec.draft_count = Booking.search_count([('state', '=', 'draft')])
            rec.review_count = Booking.search_count([('state', '=', 'under_review')])
            rec.approved_count = Booking.search_count([('state', '=', 'approved')])
            rec.rejected_count = Booking.search_count([('state', '=', 'rejected')])