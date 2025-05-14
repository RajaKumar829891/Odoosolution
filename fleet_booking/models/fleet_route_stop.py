from odoo import api, fields, models

class FleetRouteStop(models.Model):
    _name = 'fleet.route.stop'
    _description = 'Route Stop'
    _order = 'sequence, id'
    
    location = fields.Char(string='Location', required=True)
    estimated_arrival = fields.Float(string='Estimated Arrival Time')
    estimated_departure = fields.Float(string='Estimated Departure Time')
    route_id = fields.Many2one('fleet.route', string='Route', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Location Name', required=True)
    latitude = fields.Float(string='Latitude', digits=(16, 8))
    longitude = fields.Float(string='Longitude', digits=(16, 8))
    distance = fields.Float(string='Distance', digits=(16, 2))
    duration = fields.Integer(string='Duration (minutes)')
    
    # Missing fields that were identified in errors
    stop_duration = fields.Integer(string='Stop Duration (minutes)')
    passenger_count = fields.Integer(string='Passenger Count', default=0)
    
    stop_type = fields.Selection([
        ('pickup', 'Pickup'),
        ('dropoff', 'Drop-off'),
        ('waypoint', 'Waypoint'),
        ('rest', 'Rest Stop'),
    ], string='Stop Type', default='waypoint')
    
    # Computed fields based on stop_type
    is_pickup = fields.Boolean(string='Is Pickup', compute='_compute_stop_types', store=True)
    is_dropoff = fields.Boolean(string='Is Dropoff', compute='_compute_stop_types', store=True)
    
    notes = fields.Text(string='Notes')
    
    # Compute method for both is_pickup and is_dropoff fields
    @api.depends('stop_type')
    def _compute_stop_types(self):
        for record in self:
            record.is_pickup = record.stop_type == 'pickup'
            record.is_dropoff = record.stop_type == 'dropoff'