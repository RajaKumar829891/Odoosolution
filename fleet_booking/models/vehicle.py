from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FleetVehicle(models.Model):
    _name = 'fleet.vehicle'
    _description = 'Fleet Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Vehicle Name', required=True, tracking=True)
    license_plate = fields.Char(string='License Plate', required=True, tracking=True)
    vin = fields.Char(string='Chassis Number')
    
    # Vehicle details
    model = fields.Char(string='Model')
    make = fields.Char(string='Make')
    year = fields.Char(string='Year')
    color = fields.Char(string='Color')
    
    # Vehicle type
    vehicle_type = fields.Selection([
        ('26_seater_ac_coach', '26 Seater AC coach'),
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('mini_bus', 'Mini Bus'),
        ('bus', 'Bus'),
    ], string='Vehicle Type', required=True)
    
    # Capacity
    passenger_capacity = fields.Integer(string='Passenger Capacity', required=True)
    luggage_capacity = fields.Integer(string='Luggage Capacity')
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('cng', 'CNG'),
        ('lpg', 'LPG'),
    ], string='Fuel Type', default='diesel')
    
    # Amenities and features
    has_ac = fields.Boolean(string='Air Conditioning')
    has_wifi = fields.Boolean(string='WiFi')
    has_entertainment = fields.Boolean(string='Entertainment System')
    has_refreshments = fields.Boolean(string='Refreshments')
    has_usb_charging = fields.Boolean(string='USB Charging')
    has_wheelchair_access = fields.Boolean(string='Wheelchair Access')
    amenities = fields.Text(string='Other Amenities')
    
    # Status and availability
    active = fields.Boolean(string='Active', default=True, tracking=True)
    state = fields.Selection([
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Under Maintenance'),
        ('out_of_service', 'Out of Service'),
    ], string='Status', default='available', tracking=True)
    
    # Cost & booking related
    cost_per_km = fields.Float(string='Cost per Km')
    base_rental_price = fields.Float(string='Base Rental Price')
    
    # Maintenance info
    last_service_date = fields.Date(string='Last Service Date')
    next_service_date = fields.Date(string='Next Service Date')
    current_odometer = fields.Float(string='Current Odometer')
    service_interval_km = fields.Float(string='Service Interval (km)')
    service_interval_days = fields.Integer(string='Service Interval (days)')
    
    # Relations
    driver_ids = fields.Many2many('fleet.driver', string='Qualified Drivers')
    booking_ids = fields.One2many('fleet.booking', 'vehicle_id', string='Bookings')
    booking_count = fields.Integer(string='Booking Count', compute='_compute_booking_count')
    
    # Insurance & documentation
    insurance_provider = fields.Char(string='Insurance Provider')
    insurance_policy = fields.Char(string='Insurance Policy Number')
    insurance_expiry = fields.Date(string='Insurance Expiry Date')
    registration_expiry = fields.Date(string='Registration Expiry Date')
    fitness_expiry = fields.Date(string='Fitness Certificate Expiry')
    
    # Notes
    notes = fields.Text(string='Notes')
    available = fields.Boolean(string='Available', compute='_compute_available', store=True)
    
    @api.depends('booking_ids')
    def _compute_booking_count(self):
        for vehicle in self:
            vehicle.booking_count = len(vehicle.booking_ids)
    
    @api.constrains('insurance_expiry', 'registration_expiry', 'fitness_expiry')
    def _check_expiry_dates(self):
        today = fields.Date.today()
        for vehicle in self:
            if vehicle.insurance_expiry and vehicle.insurance_expiry < today:
                raise ValidationError(_("Vehicle insurance has expired!"))
            if vehicle.registration_expiry and vehicle.registration_expiry < today:
                raise ValidationError(_("Vehicle registration has expired!"))
            if vehicle.fitness_expiry and vehicle.fitness_expiry < today:
                raise ValidationError(_("Vehicle fitness certificate has expired!"))
    
    def action_view_bookings(self):
        self.ensure_one()
        return {
            'name': _('Vehicle Bookings'),
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.booking',
            'view_mode': 'tree,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
    
    def action_set_available(self):
        self.write({'state': 'available'})
    
    def action_set_in_use(self):
        self.write({'state': 'in_use'})
    
    def action_set_maintenance(self):
        self.write({'state': 'maintenance'})
    
    def action_set_out_of_service(self):
        self.write({'state': 'out_of_service'})
    @api.depends('state')
    def _compute_available(self):
        for vehicle in self:
            vehicle.available = vehicle.state == 'available'