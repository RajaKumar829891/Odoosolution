from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FleetRoute(models.Model):
    _name = 'fleet.route'
    _description = 'Fleet Route'
    
    name = fields.Char(string='Route Name', compute='_compute_name', store=True)
    start_location = fields.Char(string='Start Location', required=True)
    end_location = fields.Char(string='End Location', required=True)
    via_stops = fields.Text(string='Via Stops')
    via_stop_ids = fields.One2many('fleet.route.stop', 'route_id', string='Stops')
    
    distance = fields.Float(string='Distance', digits=(16, 2))
    distance_uom = fields.Selection([
        ('km', 'Kilometer'),
        ('mile', 'Mile')
    ], string='Distance UOM', default='km')
    
    duration = fields.Integer(string='Duration (minutes)')
    
    # For pricing and calculations
    base_price = fields.Float(string='Base Price')
    price_per_km = fields.Float(string='Price per Km/Mile')
    toll_fees = fields.Float(string='Toll Fees')
    
    # Route details
    is_round_trip = fields.Boolean(string='Round Trip')
    is_express = fields.Boolean(string='Express Route')
    complexity = fields.Selection([
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('difficult', 'Difficult'),
    ], string='Route Complexity', default='moderate')
    
    description = fields.Text(string='Route Description')
    notes = fields.Text(string='Notes')
    
    # Related bookings
    booking_ids = fields.One2many('fleet.booking', 'route_id', string='Bookings')
    
    @api.depends('start_location', 'end_location')
    def _compute_name(self):
        for route in self:
            route.name = f"{route.start_location} → {route.end_location}"
    
    @api.constrains('start_location', 'end_location')
    def _check_locations(self):
        for route in self:
            if route.start_location == route.end_location and not route.is_round_trip:
                raise ValidationError(_("Start and end locations cannot be the same unless it's a round trip."))


class FleetRouteStop(models.Model):
    _name = 'fleet.route.stop'
    _description = 'Route Stop'
    _order = 'sequence'
    
    name = fields.Char(string='Stop Name', required=True)
    route_id = fields.Many2one('fleet.route', string='Route', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    
    location = fields.Char(string='Location', required=True)
    estimated_arrival = fields.Float(string='Estimated Arrival Time')
    estimated_departure = fields.Float(string='Estimated Departure Time')
    
    stop_duration = fields.Integer(string='Stop Duration (minutes)', default=0)
    notes = fields.Text(string='Notes')
    
    # For pickup/dropoff of passengers
    is_pickup = fields.Boolean(string='Is Pickup Point')
    is_dropoff = fields.Boolean(string='Is Dropoff Point')
    passenger_count = fields.Integer(string='Passenger Count', default=0)


class FleetCargoManifest(models.Model):
    _name = 'fleet.cargo.manifest'
    _description = 'Cargo Manifest'
    
    name = fields.Char(string='Manifest Reference', required=True, copy=False, 
                       readonly=True, default=lambda self: _('New'))
    booking_id = fields.Many2one('fleet.booking', string='Booking')
    date = fields.Date(string='Date', default=fields.Date.today)
    
    cargo_line_ids = fields.One2many('fleet.cargo.line', 'manifest_id', string='Cargo Lines')
    total_weight = fields.Float(string='Total Weight', compute='_compute_totals', store=True)
    total_volume = fields.Float(string='Total Volume', compute='_compute_totals', store=True)
    total_items = fields.Integer(string='Total Items', compute='_compute_totals', store=True)
    
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('loaded', 'Loaded'),
        ('delivered', 'Delivered'),
    ], string='Status', default='draft')
    
    @api.depends('cargo_line_ids', 'cargo_line_ids.weight', 'cargo_line_ids.volume', 'cargo_line_ids.quantity')
    def _compute_totals(self):
        for manifest in self:
            manifest.total_weight = sum(manifest.cargo_line_ids.mapped('weight'))
            manifest.total_volume = sum(manifest.cargo_line_ids.mapped('volume'))
            manifest.total_items = sum(manifest.cargo_line_ids.mapped('quantity'))
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('fleet.cargo.manifest') or _('New')
        return super(FleetCargoManifest, self).create(vals_list)
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    
    def action_set_loaded(self):
        self.write({'state': 'loaded'})
    
    def action_set_delivered(self):
        self.write({'state': 'delivered'})


class FleetCargoLine(models.Model):
    _name = 'fleet.cargo.line'
    _description = 'Cargo Line'
    
    manifest_id = fields.Many2one('fleet.cargo.manifest', string='Manifest', required=True, ondelete='cascade')
    name = fields.Char(string='Description', required=True)
    cargo_type = fields.Selection([
        ('luggage', 'Luggage'),
        ('mail', 'Mail/Packages'),
        ('goods', 'Goods'),
        ('perishable', 'Perishable'),
        ('dangerous', 'Dangerous Goods'),
        ('other', 'Other'),
    ], string='Type', default='luggage', required=True)
    
    quantity = fields.Integer(string='Quantity', default=1)
    weight = fields.Float(string='Weight (kg)')
    volume = fields.Float(string='Volume (m³)')
    
    # For tracking
    tracking_number = fields.Char(string='Tracking Number')
    owner_id = fields.Many2one('res.partner', string='Owner')
    
    special_instructions = fields.Text(string='Special Instructions')
    checked = fields.Boolean(string='Checked', default=False)