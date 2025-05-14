from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Add customer-specific fields
    is_fleet_customer = fields.Boolean(string='Is Fleet Customer', default=False)
    booking_ids = fields.One2many('fleet.booking', 'customer_id', string='Bookings')
    booking_count = fields.Integer(string='Booking Count', compute='_compute_booking_count')
    
    preferred_vehicle_type = fields.Selection([
        ('26_seater_ac_coach', '26 Seater AC coach'),
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('mini_bus', 'Mini Bus'),
        ('bus', 'Bus'),
    ], string='Preferred Vehicle Type')
    
    customer_notes = fields.Text(string='Customer Notes')
    
    # For corporate customers
    billing_instructions = fields.Text(string='Billing Instructions')
    payment_terms = fields.Char(string='Payment Terms')
    credit_limit = fields.Float(string='Credit Limit')
    
    # Customer classification
    customer_type = fields.Selection([
        ('individual', 'Individual'),
        ('corporate', 'Corporate'),
        ('agency', 'Travel Agency'),
        ('vip', 'VIP'),
    ], string='Customer Type', default='individual')
    
    loyalty_points = fields.Integer(string='Loyalty Points', default=0)
    
    # Identification details
    id_type = fields.Selection([
        ('passport', 'Passport'),
        ('driving_license', 'Driving License'),
        ('national_id', 'National ID'),
        ('other', 'Other'),
    ], string='ID Type')
    id_number = fields.Char(string='ID Number')
    
    @api.depends('booking_ids')
    def _compute_booking_count(self):
        for partner in self:
            partner.booking_count = len(partner.booking_ids)
    
    def action_view_bookings(self):
        self.ensure_one()
        return {
            'name': _('Customer Bookings'),
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.booking',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.id)],
            'context': {'default_customer_id': self.id},
        }