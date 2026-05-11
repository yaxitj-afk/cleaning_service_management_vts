# -*- coding: utf-8 *-*
from odoo import http
from odoo.http import request

class CleaningController(http.Controller):

    @http.route('/cleaning', type='http', auth='user', website=True)
    def cleaning_form(self, **kwargs):
        services = request.env['service.type.vts'].sudo().search([])
        shifts = request.env['cleaning.shift.vts'].sudo().search([])

        partner = request.env.user.partner_id

        if partner and (not partner.phone or not partner.street):
            return request.redirect('/my/account?redirect=/cleaning')

        return request.render('cleaning_service_management_vts.cleaning_form_template', 
            {'services': services,'shifts': shifts,'partner': partner})

    @http.route('/cleaning/submit', type='http', auth='public', methods=['POST'], website=True)
    def cleaning_submit(self, **post):

        partner = request.env.user.partner_id

        booking_request = request.env['booking.request'].sudo().create({
            'partner_id': partner.id,
            'service_type_id': int(post.get('service_type_id')),
            'floor_count': post.get('floor_count'),
            'room_count': post.get('room_count'),
            'area_sqft': post.get('area_sqft'),
            'cleaning_shift_id': int(post.get('cleaning_shift_id')),
            'preferred_date': post.get('preferred_date') if post.get('preferred_date') else False,
            'is_recurring': True if post.get('is_recurring') else False,
            'repeat_interval': post.get('repeat_interval'),
            'recurring_type': post.get('recurring_type'),
            'special_instructions': post.get('special_instructions'),
        })

        if booking_request:
            booking_request._onchange_service_type_id()
            booking_request._onchange_partner_id()

        return request.redirect('/cleaning-thank-you')

    @http.route('/cleaning-thank-you', type='http', auth='public', website=True)
    def thank_you(self, **kwargs):
        return request.render('cleaning_service_management_vts.cleaning_thank_you')