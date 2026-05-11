# -*- coding: utf-8 *-*
from odoo import models, fields, api, _
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class CleaningBookingRequest(models.Model):
    _name = 'booking.request'
    _description = 'Cleaning Booking Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Request Reference',
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        tracking=True
    )

    mobile = fields.Char(string="Mobile No.", help="Customer Contact number")
    email = fields.Char(string="Email", help="Customer email ID")

    service_type_id = fields.Many2one(
        'service.type.vts',
        string="Service Type", tracking=True, help="Select type of services needed to cleaning"
    )

    floor_count = fields.Integer(
        string='No. of Floors',
        help="Total number of floors to be cleaned."
    )

    area_sqft = fields.Float(
        string='Area (sq.ft)',
        help="Specify the total area that needs to be cleaned, in square feet."
    )

    room_count = fields.Integer(
        string='No. of Room',
        help="Total number of rooms to be cleaned"
    )

    special_instructions = fields.Text(
        string='Special Instructions',
        copy=False,
        help="Add specific instructions or notes that should remember during the service"
    )

    preferred_date = fields.Date(
        string='Preferred Date', tracking=True,
        help='Choose preferred date for the service'
    )

    end_date = fields.Date(
        string='Ending Date', tracking=True,
        help='Choose ending date of the recurring service'
    )

    cleaning_shift_id = fields.Many2one(
        'cleaning.shift.vts',
        string="Shift Type", tracking=True,
        help="Select the shift during which the cleaning service is scheduled."
    )

    shift_slot_id = fields.Many2one(
        'cleaning.shift.slot.vts',
        string="Time Slot",
        tracking=True,
        help="Select the time slot within the selected shift."
    )

    is_individual = fields.Boolean(
        string="Assign Individual",
        help="Enable if a single employee is sufficient to complete the service."
    )
    individual_id = fields.Many2one(
        'hr.employee',
        string="Individual Cleaner",
        help="Select the employee assigned as the individual cleaner."
    )

    cleaning_team_id = fields.Many2one(
        'cleaning.team.vts',
        string="Cleaning Team",
        domain="[('cleaning_shift_id', '=', cleaning_shift_id)]",
        help="Select the cleaning team assigned for the service.",
    )

    is_recurring = fields.Boolean(
        string='Is Recurring',
        help="Enable if the service is recurring for continuous scheduling."
    )

    repeat_interval = fields.Integer(
        string="Repeat Until",
        default=1,
        help="Number of days, weeks, or months for each service repetition."
    )

    recurring_type = fields.Selection([
        ('day', 'Days'),
        ('week', 'Week'),
        ('month', 'Month'),
    ], string='Recurring Type', default='week', required=True,
        help="Select the interval type for service recurrence (days, weeks, or months).")

    pricing_type = fields.Selection([
        ('fixed', 'Fixed Price'),
        ('area_based', 'Area Based'),
    ], default='area_based', string='Pricing Type', help="Select how the service price is calculated.")

    fixed_price = fields.Float(
        string='Fixed Price', copy=False, help="Fixed price for the service."
    )

    rate_per_sqft = fields.Float(
        string='Rate per Sq.ft', help="Price charged per square foot of service area."
    )

    estimated_amount = fields.Float(
        string='Estimated Amount',
        compute='_compute_estimated_amount',
        store=True,
        help="Automatically calculated estimated total amount."
    )

    state = fields.Selection([
        ('draft', 'New Request'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', tracking=True)

    assigned_manager_id = fields.Many2one(
        'res.users',
        string='Assigned Manager', tracking=True, copy=False,
        help=" Assigned user responsible for reviewing and managing the booking request."
    )

    approved_on = fields.Datetime(string='Approved On', copy=False,
                                  help="Date and time when the request has been approved.")
    rejected_on = fields.Datetime(string='Rejected On', copy=False, help="Date and time when the request was rejected.")

    cln_task_count = fields.Integer(string="Task Count", compute="_compute_cleaning_task_count")

    invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True, copy=False)
    invoice_count = fields.Integer(string="Invoice Count", compute="_compute_invoice_count")


                                        # COMPUTE METHODS
    def _compute_cleaning_task_count(self):
        for rec in self:
            rec.cln_task_count = self.env['project.task'].search_count([('booking_id', '=', rec.id)])

    def action_booking_task(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("project.act_project_project_2_project_task_all")
        action['domain'] = [('booking_id', '=', self.id)]
        return action

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = self.env['account.move'].search_count(
                [('booking_id', '=', self.id), ('move_type', '=', 'out_invoice')])

    def action_view_invoice(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [('booking_id', '=', self.id), ('move_type', '=', 'out_invoice')]
        return action

                                        # ONCHANGE METHOD
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.mobile = self.partner_id.mobile or self.partner_id.phone
            self.email = self.partner_id.email

    @api.onchange('service_type_id')
    def _onchange_service_type_id(self):
        if self.service_type_id:
            self.rate_per_sqft = self.service_type_id.default_rate_per_sqft
            self.pricing_type = self.service_type_id.price_type
            self.fixed_price = self.service_type_id.default_fixed_price

    @api.onchange('cleaning_shift_id')
    def _onchange_cleaning_shift_id(self):
        self.shift_slot_id = False
        self.cleaning_team_id = False
        self.individual_id = False

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id:
            self.country_id = self.state_id.country_id

                                         # OTHERS METHOD
    @api.depends('pricing_type', 'fixed_price', 'area_sqft', 'rate_per_sqft')
    def _compute_estimated_amount(self):
        for rec in self:
            if rec.pricing_type == 'fixed':
                rec.estimated_amount = rec.fixed_price
            elif rec.pricing_type == 'area_based':
                rec.estimated_amount = rec.area_sqft * rec.rate_per_sqft
            else:
                rec.estimated_amount = 0.0

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('cleaning.booking.request') or _('New')
        return super().create(vals)


    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_review(self):
        for rec in self:
            if not rec.assigned_manager_id:
                raise ValidationError(
                    "Please select an Assigned Manager before sending the booking for review."
                )

            self._send_approval_email(rec)
            rec.state = 'under_review'

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'
            rec.rejected_on = fields.Datetime.now()

    # ---------------------------------------------------------------------------------------------------------------------------
    #         `                       APPROVE METHOD PROCESS
    # ---------------------------------------------------------------------------------------------------------------------------

    def action_approve(self):
        for rec in self:
            if not rec.cleaning_team_id and not rec.individual_id:
                raise ValidationError("Please select an individual cleaner or cleaning team before approving the booking request.")
            rec.approved_on = fields.Datetime.now()
            project = self.env.ref('cleaning_service_management_vts.project_cleaning_default_vts')
            description = self._prepare_description(rec)
            self._create_tasks(rec, project, description)
            self._send_approval_email(rec)
            rec.state = 'approved'

    def _prepare_description(self, rec):
        return (
            f"<b>Customer:</b> {rec.partner_id.name or ''}<br/>"
            f"<b>Mobile:</b> {rec.mobile or ''}<br/>"
            f"<b>Email:</b> {rec.email or ''}<br/><br/>"
            f"<b>Service:</b> {rec.service_type_id.name or ''}<br/>"
            f"<b>Date:</b> {rec.preferred_date or ''}<br/>"
            f"<b>Area:</b> {rec.area_sqft} sq.ft<br/>"
            f"<b>Rooms:</b> {rec.room_count}<br/>"
            f"<b>Floors:</b> {rec.floor_count}<br/><br/>"
            f"<b>Instructions:</b><br/>{rec.special_instructions}"
        )

    def _get_date_range(self, rec):
        dates = []
        current_date = rec.preferred_date
        max_tasks = 366
        count = 0
        while current_date <= rec.end_date and count < max_tasks:
            dates.append(current_date)
            current_date = self._get_next_date(rec, current_date)
            count += 1
        return dates

    def _get_next_date(self, rec, start_date):
        if rec.recurring_type == 'day':
            return start_date + timedelta(days=rec.repeat_interval)
        elif rec.recurring_type == 'week':
            return start_date + timedelta(weeks=rec.repeat_interval)
        elif rec.recurring_type == 'month':
            return start_date + relativedelta(months=rec.repeat_interval)
        raise ValidationError("Invalid recurring type.")

    @api.constrains('is_recurring', 'end_date', 'preferred_date')
    def _check_end_date(self):
        for rec in self:
            if rec.is_recurring and rec.end_date and rec.preferred_date:
                if rec.end_date <= rec.preferred_date:
                    raise ValidationError("Ending Date must be greater than Preferred Date.")

    def _get_or_create_users(self, employee_ids):
        user_ids = []
        for employee in self.env['hr.employee'].browse(employee_ids):
            if employee.user_id:
                user_ids.append(employee.user_id.id)
                continue
            action = employee.action_create_user()
            ctx = action.get('context', {})

            user = self.env['res.users'].with_context(no_reset_password=True).create({
                'name': ctx.get('default_name'),
                'login': ctx.get('default_login'),
                'mobile': ctx.get('default_mobile') or False,
                'phone': ctx.get('default_phone') or False,
                'partner_id': ctx.get('default_partner_id'),
            })

            employee.user_id = user.id
            user_ids.append(user.id)

        return user_ids

    def _get_employee_ids(self, rec):
        if rec.is_individual:
            return [rec.individual_id.id] if rec.individual_id.id else []
        return rec.cleaning_team_id.employee_ids.ids if rec.cleaning_team_id else []

    def _create_tasks(self, rec, project, description):
        employee_ids = self._get_employee_ids(rec)
        employee_user_ids = self._get_or_create_users(employee_ids)
        user_cmd = [(6, 0, employee_user_ids)]

        if not rec.is_recurring:
            task_vals_list = [{
                'name': f"Cleaning - {rec.name}",
                'project_id': project.id,
                'partner_id': rec.partner_id.id,
                'description': description,
                'date_deadline': rec.preferred_date,
                'booking_id': rec.id,
                'user_ids': user_cmd,
            }]
        else:
            date_list = self._get_date_range(rec)
            task_vals_list = [
                {
                    'name': f"Cleaning - {rec.name} ({index})",
                    'project_id': project.id,
                    'partner_id': rec.partner_id.id,
                    'description': description,
                    'date_deadline': task_date,
                    'booking_id': rec.id,
                    'user_ids': user_cmd,
                }
                for index, task_date in enumerate(date_list, start=1)
            ]

        self.env['project.task'].create(task_vals_list)

    def _send_approval_email(self, rec):
        template = False
        if rec.state == 'draft':
            template = self.env.ref('cleaning_service_management_vts.email_booking_request_notify_to_manager')
        elif rec.state == 'under_review':
            template = self.env.ref(
                'cleaning_service_management_vts.email_booking_request_approve_template_vts')

        if template:
            template.send_mail(rec.id, force_send=True)

    # ------------------------------------------------------------------------------------------------------------------------
    def create_booked_invoice(self):
        self.ensure_one()

        description = self.service_type_id.name
        price = self.estimated_amount
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_origin': self.name,
            'booking_id': self.id,
            'invoice_line_ids': [(0, 0, {
                'name': f"{description} Cleaning Service",
                'quantity': 1,
                'price_unit': price,
            })],
        }

        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice.id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
        }
