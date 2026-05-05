from odoo import models, fields


class CleaningServiceTypeVTS(models.Model):
    _name = 'service.type.vts'
    _description = 'Cleaning Service Type'
    _order = 'name'

    name = fields.Char(string='Service Type', required=True)
    description = fields.Text()

    price_type = fields.Selection([
        ('fixed', 'Fixed Price'),
        ('area_based', 'Area Based'),
    ], default='area_based' ,string='Pricing Type')
    
    default_fixed_price = fields.Float(string='Default Fixed Price')
    default_rate_per_sqft = fields.Float(string='Default Rate per Sq.ft')