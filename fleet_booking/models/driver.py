from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FleetDriver(models.Model):
    _name = 'fleet.driver'
    _description = 'Fleet Driver'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Driver Name', required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Related Employee', ondelete='set null', tracking=True)
    user_id = fields.Many2one('res.users', string='Related User', ondelete='set null')
    
    # Contact information
    mobile = fields.Char(string='Mobile', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    address = fields.Text(string='Address')
    
    # Personal identification
    identification_no = fields.Char(string='ID Number', tracking=True)
    passport_no = fields.Char(string='Passport Number')
    
    # License information
    license_number = fields.Char(string='License Number', required=True, tracking=True)
    license_type = fields.Selection([
        ('a', 'A - Motorcycle'),
        ('b', 'B - Car'),
        ('c', 'C - Commercial'),
        ('d', 'D - Bus/Coach'),
        ('e', 'E - Heavy Vehicle'),
    ], string='License Type', required=True, tracking=True)
    license_expiry = fields.Date(string='License Expiry Date', tracking=True)
    
    # Additional qualifications
    has_first_aid_cert = fields.Boolean(string='First Aid Certificate', default=False)
    has_dangerous_goods_cert = fields.Boolean(string='Dangerous Goods Certificate', default=False)
    has_passenger_transport_cert = fields.Boolean(string='Passenger Transport Certificate', default=False)
    additional_qualifications = fields.Text(string='Additional Qualifications')
    
    # Availability and status
    active = fields.Boolean(string='Active', default=True, tracking=True)
    available = fields.Boolean(string='Available Now', default=True, tracking=True)
    state = fields.Selection([
        ('available', 'Available'),
        ('on_trip', 'On Trip'),
        ('on_leave', 'On Leave'),
        ('inactive', 'Inactive'),
    ], string='Status', default='available', tracking=True)
    
    # Relations
    vehicle_ids = fields.Many2many(
        'fleet.vehicle', 
        'fleet_driver_vehicle_rel', 
        'driver_id', 
        'vehicle_id', 
        string='Qualified Vehicles'
    )
    preferred_vehicle_id = fields.Many2one(
        'fleet.vehicle', 
        string='Preferred Vehicle', 
        ondelete='set null'
    )
    booking_ids = fields.One2many(
        'fleet.booking', 
        'driver_id', 
        string='Assigned Bookings'
    )
    booking_count = fields.Integer(
        string='Booking Count', 
        compute='_compute_booking_count', 
        default=0
    )
    
    # Performance tracking
    rating = fields.Float(string='Rating', digits=(2, 1), default=5.0)
    total_trips = fields.Integer(string='Total Trips', compute='_compute_trip_stats', store=True, default=0)
    completed_trips = fields.Integer(string='Completed Trips', compute='_compute_trip_stats', store=True, default=0)
    cancelled_trips = fields.Integer(string='Cancelled Trips', compute='_compute_trip_stats', store=True, default=0)
    
    # Notes
    notes = fields.Text(string='Notes')
    
    # New fields for employee info
    employee_department_id = fields.Many2one(
        related='employee_id.department_id', 
        string='Department',
        readonly=True, 
        store=False
    )
    employee_job_id = fields.Many2one(
        related='employee_id.job_id', 
        string='Job Position',
        readonly=True, 
        store=False
    )
    employee_work_phone = fields.Char(
        related='employee_id.work_phone', 
        string='Work Phone',
        readonly=True, 
        store=False
    )
    employee_work_email = fields.Char(
        related='employee_id.work_email', 
        string='Work Email',
        readonly=True, 
        store=False
    )
    
    @api.depends('booking_ids')
    def _compute_booking_count(self):
        for driver in self:
            driver.booking_count = len(driver.booking_ids) if driver.booking_ids else 0
    
    @api.depends('booking_ids', 'booking_ids.state')
    def _compute_trip_stats(self):
        for driver in self:
            if not driver.booking_ids:
                driver.total_trips = 0
                driver.completed_trips = 0
                driver.cancelled_trips = 0
                continue
                
            driver.total_trips = len(driver.booking_ids)
            driver.completed_trips = len(driver.booking_ids.filtered(lambda b: b.state == 'completed'))
            driver.cancelled_trips = len(driver.booking_ids.filtered(lambda b: b.state == 'cancelled'))
    
    @api.constrains('license_expiry')
    def _check_license_expiry(self):
        for driver in self:
            if driver.license_expiry and driver.license_expiry < fields.Date.today():
                raise ValidationError(_("The driver's license has expired!"))
    
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """
        Auto-fill driver information when an employee is selected
        """
        if self.employee_id:
            self.name = self.employee_id.name
            # Use employee mobile phone, or work phone as fallback
            self.mobile = self.employee_id.mobile_phone or self.employee_id.work_phone or self.mobile
            self.email = self.employee_id.work_email or self.email
            
            # If employee has a user, link it 
            if self.employee_id.user_id:
                self.user_id = self.employee_id.user_id.id
                
            # You can add more mappings here as needed
            # For example, if employee module has address information:
            if hasattr(self.employee_id, 'address_home_id') and self.employee_id.address_home_id:
                address_parts = []
                address = self.employee_id.address_home_id
                if address.street:
                    address_parts.append(address.street)
                if address.street2:
                    address_parts.append(address.street2)
                if address.city:
                    address_parts.append(address.city)
                if address.state_id:
                    address_parts.append(address.state_id.name)
                if address.zip:
                    address_parts.append(address.zip)
                if address.country_id:
                    address_parts.append(address.country_id.name)
                
                if address_parts:
                    self.address = ", ".join(address_parts)
    
    def action_view_bookings(self):
        self.ensure_one()
        return {
            'name': _('Driver Bookings'),
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.booking',
            'view_mode': 'tree,form',
            'domain': [('driver_id', '=', self.id)],
            'context': {'default_driver_id': self.id},
        }
    
    def action_set_available(self):
        self.write({'state': 'available', 'available': True})
    
    def action_set_on_trip(self):
        self.write({'state': 'on_trip', 'available': False})
    
    def action_set_on_leave(self):
        self.write({'state': 'on_leave', 'available': False})
    
    def action_set_inactive(self):
        self.write({'state': 'inactive', 'available': False, 'active': False})