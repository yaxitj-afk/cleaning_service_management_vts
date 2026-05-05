from odoo import http
from odoo.http import request

class BookingDashboard(http.Controller):

    @http.route('/booking/dashboard/data', type='json', auth='user')
    def dashboard_data(self):
        return request.env['booking.request'].get_dashboard_data()