from odoo import models, fields, api
from odoo.exceptions import UserError

class SimplyFleetFuelLog(models.Model):
    _inherit = 'simply.fleet.fuel.log'
    
    # Add relation to diesel tanker dispensing
    tanker_dispensing_id = fields.Many2one('simply.fleet.tanker.dispensing', string='Tanker Dispensing', readonly=True)
    
    # Add relation to diesel tanker
    diesel_tanker_id = fields.Many2one('simply.fleet.diesel.tanker', string='Diesel Tanker Source', 
                                      domain="[('current_fuel_level', '>', 0)]")
    
    # Override create method to automatically reduce diesel tanker fuel level
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Only process diesel tanker fuel logs
            if vals.get('station_type') == 'diesel_tanker' and vals.get('fuel_type') == 'diesel':
                # If tanker ID is provided
                if vals.get('diesel_tanker_id'):
                    tanker = self.env['simply.fleet.diesel.tanker'].browse(vals.get('diesel_tanker_id'))
                else:
                    # Find the tanker with highest fuel level if not specified
                    tanker = self.env['simply.fleet.diesel.tanker'].search([
                        ('current_fuel_level', '>', 0)
                    ], order='current_fuel_level DESC', limit=1)
                    
                    if tanker:
                        vals['diesel_tanker_id'] = tanker.id
                    else:
                        raise UserError("No diesel tanker with fuel available. Please refill a tanker first.")
                
                # Check if there's enough fuel in the tanker
                liters = vals.get('liters', 0)
                if tanker.current_fuel_level < liters:
                    raise UserError(f"Not enough fuel in tanker '{tanker.name}'. Current level: {tanker.current_fuel_level} L, Requested: {liters} L")
                
                # Create a dispensing record
                dispensing_vals = {
                    'tanker_id': tanker.id,
                    'date': vals.get('datetime', fields.Datetime.now()),
                    'vehicle_id': vals.get('vehicle_id'),
                    'quantity': liters,
                    'odometer': vals.get('odometer', 0),
                    'notes': vals.get('notes', 'Created from fuel log')
                }
                
                dispensing = self.env['simply.fleet.tanker.dispensing'].with_context(from_fuel_log=True).create(dispensing_vals)
                vals['tanker_dispensing_id'] = dispensing.id
                
                # Update tanker fuel level
                tanker.current_fuel_level -= liters
                
        # Call the original method to create the record
        return super(SimplyFleetFuelLog, self).create(vals_list)
    
    # Add diesel tanker field to form view when station type is diesel tanker
    @api.onchange('station_type')
    def _onchange_station_type(self):
        # Set fuel type as diesel when station type is diesel tanker
        if self.station_type == 'diesel_tanker':
            self.fuel_type = 'diesel'
            
            # Find tanker with highest fuel level
            tanker = self.env['simply.fleet.diesel.tanker'].search([
                ('current_fuel_level', '>', 0)
            ], order='current_fuel_level DESC', limit=1)
            
            if tanker:
                self.diesel_tanker_id = tanker.id
        else:
            self.diesel_tanker_id = False
    
    # Button action to open tanker dispensing form
    def action_open_tanker_dispensing(self):
        self.ensure_one()
        if self.tanker_dispensing_id:
            return {
                'name': 'Tanker Dispensing',
                'type': 'ir.actions.act_window',
                'res_model': 'simply.fleet.tanker.dispensing',
                'view_mode': 'form',
                'res_id': self.tanker_dispensing_id.id,
                'target': 'current',
            }
        else:
            return {
                'name': 'Diesel Tankers',
                'type': 'ir.actions.act_window',
                'res_model': 'simply.fleet.diesel.tanker',
                'views': [[False, 'tree'], [False, 'form']],
                'target': 'current',
            }
    
    # Action for button in fuel logs list view
    def action_diesel_tanker(self):
        """Action to open the diesel tanker view"""
        return {
            'name': 'Diesel Tankers',
            'type': 'ir.actions.act_window',
            'res_model': 'simply.fleet.diesel.tanker',
            'views': [[False, 'kanban'], [False, 'tree'], [False, 'form']],
            'target': 'current',
        }
