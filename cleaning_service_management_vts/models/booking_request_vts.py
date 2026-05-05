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

    mobile = fields.Char(string="Mobile No.")
    email = fields.Char(string="Email")

    service_type_id = fields.Many2one(
        'service.type.vts',
        string="Service Type", tracking=True
    )

    address = fields.Char(string="Address")
    city = fields.Char(string="City")
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    pincode = fields.Char(string="Pincode")

    floor_count = fields.Integer(
        string='No. of Floors'
    )

    area_sqft = fields.Float(
        string='Area (sq.ft)',
    )

    room_count = fields.Integer(
        string='No. of Room'
    )

    special_instructions = fields.Text(
        string='Special Instructions'
    )

    preferred_date = fields.Date(
        string='Preferred Date', tracking=True
    )

    preferred_time = fields.Float(
        string='Preferred Time (Hour Format)'
    )

    cleaning_shift_id = fields.Many2one(
        'cleaning.shift.vts',
        string="Shift Type", tracking=True
    )
    is_individual = fields.Boolean(
        string="Assign Individual"
    )
    individual_id = fields.Many2one(
        'hr.employee',
        string="Individual Cleaner"
    )

    cleaning_team_id = fields.Many2one(
        'cleaning.team.vts',
        string="Cleaning Team",
        domain="[('cleaning_shift_id', '=', cleaning_shift_id)]"
    )

    is_recurring = fields.Boolean(
        string='Is Recurring'
    )

    repeat_interval = fields.Integer(
        string="Repeat Every",
        default=1
    )

    recurring_type = fields.Selection([
        ('day', 'Days'),
        ('week', 'Week'),
        ('month', 'Month'),
        ('year', 'Years'),
    ], string='Recurring Type', default='week', required=True)

    start_recurring_date = fields.Date(
        string="Starting Date",
    )

    pricing_type = fields.Selection([
        ('fixed', 'Fixed Price'),
        ('area_based', 'Area Based'),
    ], deafult='area_based' ,string='Pricing Type')

    fixed_price = fields.Float(
        string='Fixed Price'
    )

    rate_per_sqft = fields.Float(
        string='Rate per Sq.ft',
    )

    estimated_amount = fields.Float(
        string='Estimated Amount',
        compute='_compute_estimated_amount',
        store=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft' , tracking=True)

    assigned_manager_id = fields.Many2one(
        'res.users',
        string='Assigned Manager', tracking=True
    )

    approved_on = fields.Datetime(string='Approved On')
    rejected_on = fields.Datetime(string='Rejected On')

    estimated_duration = fields.Float(string='Estimated Duration (Hours)')
    cln_task_count = fields.Integer(string="Task Count", compute="_compute_cleaning_task_count")

    def _compute_cleaning_task_count(self):
        for rec in self:
            rec.cln_task_count = self.env['project.task'].search_count([('booking_id', '=', rec.id)])

    def action_booking_task(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("project.act_project_project_2_project_task_all")
        action['domain'] = [('booking_id', '=', self.id)]
        return action

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.address = self.partner_id.street or self.partner_id.street2
            self.city = self.partner_id.city
            self.state_id = self.partner_id.state_id
            self.country_id = self.partner_id.country_id
            self.pincode = self.partner_id.zip
            self.mobile = self.partner_id.mobile or self.partner_id.phone
            self.email = self.partner_id.email

    @api.onchange('service_type_id')
    def _onchange_service_type_id(self):
        if self.service_type_id:
            self.rate_per_sqft = self.service_type_id.default_rate_per_sqft
            self.pricing_type = self.service_type_id.price_type
            self.fixed_price = self.service_type_id.default_fixed_price


    @api.depends('pricing_type', 'fixed_price', 'area_sqft', 'rate_per_sqft')
    def _compute_estimated_amount(self):
        for rec in self:
            if rec.pricing_type == 'fixed':
                rec.estimated_amount = rec.fixed_price
            elif rec.pricing_type == 'area_based':
                rec.estimated_amount = rec.area_sqft * rec.rate_per_sqft
            else:
                rec.estimated_amount = 0.0

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id:
            self.country_id = self.state_id.country_id

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
            rec.state = 'under_review'

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'
            rec.rejected_on = fields.Datetime.now()

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
            rec.approved_on = fields.Datetime.now()
            project = self.env.ref('cleaning_service_management_vts.project_cleaning_default_vts',
                                   raise_if_not_found=False)
            description = self._prepare_description(rec)
            self._create_tasks(rec, project, description)
            self._send_approval_email(rec)

    def _prepare_description(self, rec):
        return (
            f"<b>Customer:</b> {rec.partner_id.name or ''}<br/>"
            f"<b>Mobile:</b> {rec.mobile or ''}<br/>"
            f"<b>Email:</b> {rec.email or ''}<br/><br/>"

            f"<b>Service:</b> {rec.service_type_id.name or ''}<br/>"
            f"<b>Date:</b> {rec.preferred_date or ''}<br/>"
            f"<b>Time:</b> {rec.preferred_time or ''}<br/><br/>"

            f"<b>Address:</b><br/>{rec.address or ''}, {rec.city or ''}<br/><br/>"

            f"<b>Area:</b> {rec.area_sqft or 0} sq.ft<br/>"
            f"<b>Rooms:</b> {rec.room_count or 0}<br/>"
            f"<b>Floors:</b> {rec.floor_count or 0}<br/><br/>"

            f"<b>Instructions:</b><br/>{rec.special_instructions or 'N/A'}"
        )

    def _get_employee_ids(self, rec):

        if rec.is_individual:
            return rec.individual_id.id and [rec.individual_id.id] or []

        return rec.cleaning_team_id.employee_ids.ids if rec.cleaning_team_id else []

    def _create_single_task(self, rec, project, description, deadline, index):

        vals = {
            'name': f"Cleaning - {rec.name} ({index})" if rec.is_recurring else f"Cleaning - {rec.name}",
            'project_id': project.id,
            'partner_id': rec.partner_id.id,
            'description': description,
            'date_deadline': deadline,
            'booking_id': rec.id,
            'employee_ids': [(6, 0, self._get_employee_ids(rec))],
        }

        self.env['project.task'].create(vals)

    def _compute_deadline(self, rec, start_date, index):

        if rec.recurring_type == 'day':
            return start_date + timedelta(days=index)

        elif rec.recurring_type == 'week':
            return start_date + timedelta(weeks=index)

        elif rec.recurring_type == 'month':
            return start_date + relativedelta(months=index)

        elif rec.recurring_type == 'year':
            return start_date + relativedelta(years=index)

        raise ValidationError("Invalid recurring type.")

    def _create_tasks(self, rec, project, description):

        if not rec.is_recurring:
            self._create_single_task(rec, project, description, rec.preferred_date, 1)
            return

        if rec.repeat_interval <= 0:
            raise ValidationError("Number of Services must be greater than 0.")

        start_date = rec.start_recurring_date

        for i in range(rec.repeat_interval):
            deadline = self._compute_deadline(rec, start_date, i)

            self._create_single_task(rec,project,description,deadline,i + 1)

    def _send_approval_email(self, rec):

        mail_values = {
            'subject': f"Your Cleaning Booking is Approved - {rec.name}",
            'body_html': f"""
                <p>Dear {rec.partner_id.name},</p>

                <p>Your cleaning booking has been <b>APPROVED</b>.</p>

                <p>
                    <b>Booking Reference:</b> {rec.name}<br/>
                    <b>Service:</b> {rec.service_type_id.name or ''}<br/>
                    <b>Date:</b> {rec.preferred_date or ''}<br/>
                </p>

                <p>Thank you,<br/>Team</p>
            """,
            'email_from': self.env.user.email or rec.company_id.email,
            'email_to': rec.email,
            'auto_delete': True,
        }

        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        # template = self.env.ref(
        #     'cleaning_service_management_vts.email_template_cleaning_booking_approved_vts',
        #     raise_if_not_found=False
        # )
        # print('emnail template id ',template.id)
        #
        # if template:
        #     template.send_mail(rec.id, force_send=True

# ===================================================================================================================
#                             DASHBOARD METHODS
    @api.model
    def get_dashboard_data(self):
        return {
            'draft': self.search_count([('state', '=', 'draft')]),
            'under_review': self.search_count([('state', '=', 'under_review')]),
            'approved': self.search_count([('state', '=', 'approved')]),
            'rejected': self.search_count([('state', '=', 'rejected')]),
        }

    @api.model
    def get_service_analysis(self, period):
        today = fields.Date.today()

        if period == "7d":
            start_date = today - timedelta(days=7)
        elif period == "month":
            start_date = today.replace(day=1)
        else:
            start_date = today.replace(month=1, day=1)

        data = self.read_group(
            domain=[("create_date", ">=", fields.Date.to_string(start_date))],
            fields=["service_type_id"],
            groupby=["service_type_id"]
        )

        result = []
        for line in data:
            if line.get("service_type_id"):
                result.append({
                    "service": line["service_type_id"][1],
                    "count": line["service_type_id_count"],
                })

        return result