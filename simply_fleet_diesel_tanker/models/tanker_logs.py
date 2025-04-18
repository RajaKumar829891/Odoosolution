from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class SimplyFleetTankerRefill(models.Model):
    _name = 'simply.fleet.tanker.refill'
    _description = 'Diesel Tanker Refill'
    _order = 'date desc'
    
    name = fields.Char(string='Reference', readonly=True, copy=False, default='New')
    tanker_id = fields.Many2one('simply.fleet.diesel.tanker', string='Tanker', required=True, ondelete='cascade')
    date = fields.Datetime(string='Refill Date', required=True, default=fields.Datetime.now)
    quantity = fields.Float(string='Quantity (Liters)', required=True)
    vendor = fields.Char(string='Vendor')
    cost = fields.Float(string='Cost')
    notes = fields.Text(string='Notes')
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user.id, readonly=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('simply.fleet.tanker.refill') or 'New'
                
            # Update the tanker's fuel level
            tanker = self.env['simply.fleet.diesel.tanker'].browse(vals.get('tanker_id'))
            if tanker:
                # Check if adding this refill would exceed capacity
                new_level = tanker.current_fuel_level + vals.get('quantity', 0)
                if new_level > tanker.capacity:
                    raise UserError(f"Cannot refill. The tanker capacity ({tanker.capacity} L) would be exceeded.")
                
                tanker.write({
                    'current_fuel_level': new_level
                })
                
        return super().create(vals_list)


class SimplyFleetTankerDispensing(models.Model):
    _name = 'simply.fleet.tanker.dispensing'
    _description = 'Diesel Tanker Dispensing'
    _order = 'date desc'
    
    name = fields.Char(string='Reference', readonly=True, copy=False, default='New')
    tanker_id = fields.Many2one('simply.fleet.diesel.tanker', string='Tanker', required=True, ondelete='cascade')
    date = fields.Datetime(string='Dispensing Date', required=True, default=fields.Datetime.now)
    vehicle_id = fields.Many2one('simply.fleet.vehicle', string='Vehicle', required=True)
    quantity = fields.Float(string='Quantity (Liters)', required=True)
    odometer = fields.Float(string='Vehicle Odometer', required=True)
    notes = fields.Text(string='Notes')
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user.id, readonly=True)
    fuel_log_id = fields.Many2one('simply.fleet.fuel.log', string='Related Fuel Log', readonly=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('simply.fleet.tanker.dispensing') or 'New'
                
            # Update the tanker's fuel level
            tanker = self.env['simply.fleet.diesel.tanker'].browse(vals.get('tanker_id'))
            quantity = vals.get('quantity', 0)
            
            if tanker:
                # Check if we have enough fuel
                if tanker.current_fuel_level < quantity:
                    raise UserError(f"Not enough fuel in tanker. Current level: {tanker.current_fuel_level} L")
                
                # Update tanker fuel level - this is now handled in the fuel_log create method
                # to avoid double reduction when created from a fuel log
                if not self.env.context.get('from_fuel_log'):
                    tanker.write({
                        'current_fuel_level': tanker.current_fuel_level - quantity
                    })
                
                # Create fuel log entry only if not created from a fuel log
                vehicle_id = vals.get('vehicle_id')
                if vehicle_id and not self.env.context.get('from_fuel_log'):
                    # Get previous odometer
                    vehicle = self.env['simply.fleet.vehicle'].browse(vehicle_id)
                    previous_log = self.env['simply.fleet.fuel.log'].search([
                        ('vehicle_id', '=', vehicle_id),
                        ('odometer', '!=', False)
                    ], order='datetime desc, id desc', limit=1)
                    
                    previous_odometer = previous_log.odometer if previous_log else vehicle.initial_odometer or 0.0
                    
                    # Create fuel log
                    fuel_log = self.env['simply.fleet.fuel.log'].with_context(from_dispensing=True).create({
                        'vehicle_id': vehicle_id,
                        'datetime': vals.get('date'),
                        'liters': quantity,
                        'odometer': vals.get('odometer'),
                        'previous_odometer': previous_odometer,
                        'price_per_liter': 0,  # Could be updated with actual price if needed
                        'total_amount': 0,      # Could be calculated based on price
                        'fuel_type': 'diesel',
                        'fill_type': 'full',
                        'station_type': 'diesel_tanker',
                        'notes': vals.get('notes', ''),
                        'diesel_tanker_id': tanker.id
                    })
                    
                    # Link fuel log to dispensing record
                    vals['fuel_log_id'] = fuel_log.id
                
        return super().create(vals_list)