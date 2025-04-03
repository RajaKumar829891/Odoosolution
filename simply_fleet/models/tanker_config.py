from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class SimplyFleetTankerConfig(models.Model):
    _name = 'simply.fleet.tanker.config'
    _description = 'Diesel Tanker Configuration'
    
    total_capacity = fields.Float(
        string='Total Capacity (L)',
        default=1120.0,
        required=True,
        help='Total capacity of the diesel tanker in liters'
    )
    
    # Modified field to set a default and make it readonly
    tanker_vehicle_id = fields.Many2one(
        'simply.fleet.vehicle',
        string='Tanker Vehicle',
        default=lambda self: self._get_default_tanker_vehicle(),
        readonly=True,  # This makes it unchangeable in the UI
        required=True,  # Makes the field required
        help='Vehicle representing the diesel tanker'
    )
    
    remaining_capacity = fields.Float(
        string='Remaining Capacity (L)',
        compute='_compute_remaining_capacity',
        store=True,
        help='Current fuel level in the diesel tanker'
    )
    
    fuel_level_status = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Fuel Level Status', 
       compute='_compute_fuel_level_status',
       store=True)
    
    last_refill_date = fields.Datetime(
        string='Last Refill Date',
        compute='_compute_last_refill_date',
        store=True,
        help='Date and time of the last tanker refill'
    )
    
    last_refill_amount = fields.Float(
        string='Last Refill Amount (L)',
        compute='_compute_last_refill_date',
        store=True,
        help='Amount of diesel added in the last refill'
    )
    
    last_week_consumption = fields.Float(
        string='Last 7 Days Consumption (L)',
        compute='_compute_consumption_stats',
        store=True,
        help='Total diesel consumed in the last 7 days'
    )
    
    last_month_consumption = fields.Float(
        string='Last 30 Days Consumption (L)',
        compute='_compute_consumption_stats',
        store=True,
        help='Total diesel consumed in the last 30 days'
    )
    
    avg_daily_consumption = fields.Float(
        string='Average Daily Consumption (L)',
        compute='_compute_consumption_stats',
        store=True,
        help='Average daily diesel consumption based on last 30 days'
    )
    
    days_remaining = fields.Integer(
        string='Estimated Days Remaining',
        compute='_compute_days_remaining',
        store=True,
        help='Estimated number of days before the tanker is empty based on average consumption'
    )
    
    critical_level = fields.Float(
        string='Critical Level (L)',
        default=400.0,
        help='Level at which the tanker should be refilled'
    )
    
    warning_level = fields.Float(
        string='Warning Level (L)',
        default=800.0,
        help='Level at which a warning should be displayed'
    )
    
    # New method to find the default tanker vehicle
    @api.model
    def _get_default_tanker_vehicle(self):
        # Find the vehicle with name 'Diesel Tanker'
        tanker = self.env['simply.fleet.vehicle'].search([('name', '=', 'Diesel Tanker')], limit=1)
        if tanker:
            return tanker.id
        return False
    
    # Optional: Add a constraint to ensure the tanker vehicle is not changed
    @api.constrains('tanker_vehicle_id')
    def _check_tanker_vehicle(self):
        for record in self:
            if record.id and record.tanker_vehicle_id:
                original = self.browse(record.id)
                if original.tanker_vehicle_id and original.tanker_vehicle_id != record.tanker_vehicle_id:
                    raise UserError("You cannot change the tanker vehicle once it is set.")
    
    @api.depends('total_capacity', 'tanker_vehicle_id')
    def _compute_remaining_capacity(self):
        for record in self:
            # Start with full capacity
            remaining = record.total_capacity
            
            if record.tanker_vehicle_id:
                # Log for debugging
                _logger.info("Computing remaining capacity for tanker vehicle: %s", record.tanker_vehicle_id.name)
                _logger.info("Starting with total capacity: %s", remaining)
                
                # Get all fuel logs for other vehicles that were filled from the tanker
                outgoing_logs = self.env['simply.fleet.fuel.log'].search([
                    ('station_type', '=', 'diesel_tanker'),
                    ('fuel_type', '=', 'diesel'),
                    ('vehicle_id', '!=', record.tanker_vehicle_id.id)
                ])
                
                # Log outgoing details
                _logger.info("Found %s outgoing fuel logs", len(outgoing_logs))
                
                # Subtract all the fuel that was dispensed from the tanker
                for log in outgoing_logs:
                    remaining -= log.liters
                    _logger.info("Subtracted %s liters for vehicle %s, remaining: %s", 
                               log.liters, log.vehicle_id.name, remaining)
                
                # Add all refills of the tanker itself (when the tanker gets fuel from petrol pump)
                incoming_logs = self.env['simply.fleet.fuel.log'].search([
                    ('vehicle_id', '=', record.tanker_vehicle_id.id),
                    ('station_type', '=', 'petrol_pump'),
                    ('fuel_type', '=', 'diesel')
                ])
                
                # Log incoming details
                _logger.info("Found %s incoming refill logs", len(incoming_logs))
                
                for log in incoming_logs:
                    remaining += log.liters
                    _logger.info("Added %s liters from refill, remaining: %s", 
                               log.liters, remaining)
            
            # Ensure remaining capacity is not negative and doesn't exceed total capacity
            record.remaining_capacity = max(0, min(remaining, record.total_capacity))
            _logger.info("Final remaining capacity: %s", record.remaining_capacity)
    
    @api.depends('remaining_capacity', 'warning_level', 'critical_level')
    def _compute_fuel_level_status(self):
        for record in self:
            if record.remaining_capacity >= record.warning_level:
                record.fuel_level_status = 'high'
            elif record.remaining_capacity >= record.critical_level:
                record.fuel_level_status = 'medium'
            else:
                record.fuel_level_status = 'low'
    
    @api.depends('tanker_vehicle_id')
    def _compute_last_refill_date(self):
        for record in self:
            record.last_refill_date = False
            record.last_refill_amount = 0.0
            
            if record.tanker_vehicle_id:
                # Get the most recent refill of the tanker
                last_refill = self.env['simply.fleet.fuel.log'].search([
                    ('vehicle_id', '=', record.tanker_vehicle_id.id),
                    ('station_type', '=', 'petrol_pump'),
                    ('fuel_type', '=', 'diesel')
                ], order='datetime desc', limit=1)
                
                if last_refill:
                    record.last_refill_date = last_refill.datetime
                    record.last_refill_amount = last_refill.liters
    
    @api.depends('tanker_vehicle_id')
    def _compute_consumption_stats(self):
        for record in self:
            record.last_week_consumption = 0.0
            record.last_month_consumption = 0.0
            record.avg_daily_consumption = 0.0
            
            if record.tanker_vehicle_id:
                now = fields.Datetime.now()
                week_ago = now - timedelta(days=7)
                month_ago = now - timedelta(days=30)
                
                # Get consumption from the tanker in the last week and month
                week_logs = self.env['simply.fleet.fuel.log'].search([
                    ('station_type', '=', 'diesel_tanker'),
                    ('fuel_type', '=', 'diesel'),
                    ('datetime', '>=', week_ago)
                ])
                
                month_logs = self.env['simply.fleet.fuel.log'].search([
                    ('station_type', '=', 'diesel_tanker'),
                    ('fuel_type', '=', 'diesel'),
                    ('datetime', '>=', month_ago)
                ])
                
                record.last_week_consumption = sum(log.liters for log in week_logs)
                record.last_month_consumption = sum(log.liters for log in month_logs)
                
                # Calculate average daily consumption
                if record.last_month_consumption > 0:
                    record.avg_daily_consumption = record.last_month_consumption / 30
                elif record.last_week_consumption > 0:
                    record.avg_daily_consumption = record.last_week_consumption / 7
    
    @api.depends('remaining_capacity', 'avg_daily_consumption')
    def _compute_days_remaining(self):
        for record in self:
            if record.avg_daily_consumption and record.avg_daily_consumption > 0:
                record.days_remaining = int(record.remaining_capacity / record.avg_daily_consumption)
            else:
                record.days_remaining = 0
    
    @api.model
    def get_tanker_status(self):
        """Get the current status of the diesel tanker for use in client actions"""
        config = self.search([], limit=1)
        if not config:
            # If creating a new config, make sure it uses the default tanker vehicle
            config = self.create({})
            
        return {
            'remaining': config.remaining_capacity,
            'total': config.total_capacity,
            'status': config.fuel_level_status,
            'days_remaining': config.days_remaining,
            'last_refill_date': config.last_refill_date,
            'last_refill_amount': config.last_refill_amount,
            'avg_daily_consumption': config.avg_daily_consumption
        }
    
    def action_recalculate_capacity(self):
        """Manually trigger recalculation of capacity and statistics"""
        self.invalidate_model(['remaining_capacity', 'fuel_level_status', 
                           'last_refill_date', 'last_refill_amount',
                           'last_week_consumption', 'last_month_consumption',
                           'avg_daily_consumption', 'days_remaining'])
        
        # Force recomputation by adding to compute and flushing
        self.env.add_to_compute(self._fields['remaining_capacity'], self)
        self.env.add_to_compute(self._fields['fuel_level_status'], self)
        self.env.add_to_compute(self._fields['last_refill_date'], self)
        self.env.add_to_compute(self._fields['last_refill_amount'], self)
        self.env.add_to_compute(self._fields['last_week_consumption'], self)
        self.env.add_to_compute(self._fields['last_month_consumption'], self)
        self.env.add_to_compute(self._fields['avg_daily_consumption'], self)
        self.env.add_to_compute(self._fields['days_remaining'], self)
        self.env.flush_all()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Diesel Tanker',
                'message': 'Statistics recalculated successfully',
                'type': 'success',
            }
        }
    
    def action_low_fuel_alert(self):
        """Send notification to managers about low fuel level"""
        if self.remaining_capacity < self.critical_level:
            # Get fleet managers or users with access to the module
            manager_group = self.env.ref('simply_fleet.group_fleet_manager', False)
            recipients = []
            
            if manager_group:
                recipients = manager_group.users.mapped('partner_id')
            
            if recipients:
                # Create a message in Odoo's chatter
                self.message_post(
                    body=f"<p>⚠️ <strong>LOW FUEL ALERT</strong> ⚠️</p>"
                         f"<p>Diesel Tanker fuel level is critically low: {self.remaining_capacity} L remaining.</p>"
                         f"<p>Estimated days remaining: {self.days_remaining}</p>",
                    partner_ids=[(6, 0, [r.id for r in recipients])],
                    message_type='notification',
                    subtype_id=self.env.ref('mail.mt_comment').id
                )
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Alert Sent',
                        'message': 'Low fuel alert notification sent to fleet managers',
                        'type': 'success',
                    }
                }
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'No Alert Needed',
                'message': 'Fuel level is above critical threshold',
                'type': 'info',
            }
        }
