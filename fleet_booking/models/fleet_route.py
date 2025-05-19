from odoo import api, fields, models, _

class FleetRoute(models.Model):
    _name = 'fleet.route'
    _description = 'Fleet Route'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Route Name', compute='_compute_name', store=True)
    start_location = fields.Char(string='Start Location', required=True, tracking=True)
    end_location = fields.Char(string='End Location', required=True, tracking=True)
    via_stops = fields.Text(string='Via Stops')
    stop_ids = fields.One2many('fleet.route.stop', 'route_id', string='Stops')
    pricing_notes = fields.Text(string='Pricing Notes')
    route_notes = fields.Text(string='Route Notes')
    
    # Route details
    distance = fields.Float(string='Distance', digits=(16, 2))
    distance_uom = fields.Selection([
        ('km', 'Kilometer'),
        ('mile', 'Mile')
    ], string='Distance UOM', default='km')
    duration = fields.Integer(string='Duration (minutes)')
    
    # Route options
    is_round_trip = fields.Boolean(string='Round Trip')  # Changed from round_trip to is_round_trip
    express_route = fields.Boolean(string='Express Route')
    route_complexity = fields.Selection([
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High')
    ], string='Route Complexity', default='moderate')
    
    # Google Maps fields
    start_latitude = fields.Float(string='Start Latitude', digits=(16, 8))
    start_longitude = fields.Float(string='Start Longitude', digits=(16, 8))
    end_latitude = fields.Float(string='End Latitude', digits=(16, 8))
    end_longitude = fields.Float(string='End Longitude', digits=(16, 8))
    polyline = fields.Text(string='Route Polyline')
    
    # Bookings using this route
    booking_ids = fields.One2many('fleet.booking', 'route_id', string='Bookings')
    booking_count = fields.Integer(string='Booking Count', compute='_compute_booking_count', store=True)

    base_price = fields.Float(string='Base Price', digits=(16, 2))
    price_per_km = fields.Float(string='Price per Kilometer', digits=(16, 2))
    toll_fees = fields.Float(string='Toll Fees', digits=(16, 2))

    description = fields.Text(string='Description')
    notes = fields.Text(string='Notes')
    
    @api.depends('start_location', 'end_location')
    def _compute_name(self):
        for route in self:
            if route.start_location and route.end_location:
                route.name = f"{route.start_location} → {route.end_location}"
            else:
                route.name = "New Route"
    
    @api.depends('booking_ids')
    def _compute_booking_count(self):
        for route in self:
            route.booking_count = len(route.booking_ids) if route.booking_ids else 0
    
    def action_view_bookings(self):
        self.ensure_one()
        return {
            'name': _('Route Bookings'),
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.booking',
            'view_mode': 'tree,form',
            'domain': [('route_id', '=', self.id)],
            'context': {'default_route_id': self.id},
        }
    
    def action_get_route_details(self):
        """Get route details from Google Maps or other service"""
        self.ensure_one()
        # Here you'd call an external API to get route details
        # For now, just update with sample data
        self.write({
            'distance': 150.0,
            'duration': 180  # 3 hours
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Route Updated'),
                'message': _('Route details have been updated.'),
                'sticky': False,
                'type': 'success',
            }
        }
    
    def action_view_on_map(self):
        """Open a Google Maps view of the route"""
        self.ensure_one()
        base_url = "https://www.google.com/maps/dir/"
        origin = self.start_location.replace(' ', '+')
        destination = self.end_location.replace(' ', '+')
        url = f"{base_url}{origin}/{destination}"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }