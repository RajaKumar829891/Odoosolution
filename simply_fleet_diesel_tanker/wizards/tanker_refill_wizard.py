# Model changes
from odoo import models, fields, api
from odoo.exceptions import UserError

class SimplyFleetTankerRefillWizard(models.TransientModel):
    _name = 'simply.fleet.tanker.refill.wizard'
    _description = 'Diesel Tanker Refill Wizard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    tanker_id = fields.Many2one('simply.fleet.diesel.tanker', string='Tanker', required=True, readonly=True)
    quantity = fields.Float(string='Quantity (Liters)', required=True)
    vendor = fields.Char(string='Vendor')
    cost = fields.Float(string='Cost')
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    notes = fields.Text(string='Notes')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    
    current_level = fields.Float(related='tanker_id.current_fuel_level', string='Current Level')
    capacity = fields.Float(related='tanker_id.capacity', string='Total Capacity')
    new_level = fields.Float(string='New Level', compute='_compute_new_level')
    
    @api.depends('current_level', 'quantity')
    def _compute_new_level(self):
        for wizard in self:
            wizard.new_level = wizard.current_level + wizard.quantity
    
    def action_refill(self):
        """Perform the refill operation"""
        self.ensure_one()
        
        # Check capacity
        if self.new_level > self.capacity:
            raise UserError(f"Cannot refill. The tanker capacity ({self.capacity} L) would be exceeded.")
        
        # Create refill log
        refill = self.env['simply.fleet.tanker.refill'].create({
            'tanker_id': self.tanker_id.id,
            'date': self.date,
            'quantity': self.quantity,
            'vendor': self.vendor,
            'cost': self.cost,
            'notes': self.notes
        })
        
        # Link attachments to the created refill record
        if self.attachment_ids:
            for attachment in self.attachment_ids:
                attachment.write({
                    'res_model': 'simply.fleet.tanker.refill',
                    'res_id': refill.id,
                })
        
        return {
            'type': 'ir.actions.act_window_close'
        }


class SimplyFleetTankerDispensingWizard(models.TransientModel):
    _name = 'simply.fleet.tanker.dispensing.wizard'
    _description = 'Diesel Tanker Dispensing Wizard'
    
    tanker_id = fields.Many2one('simply.fleet.diesel.tanker', string='Tanker', required=True, readonly=True)
    vehicle_id = fields.Many2one('simply.fleet.vehicle', string='Vehicle', required=True)
    quantity = fields.Float(string='Quantity (Liters)', required=True)
    odometer = fields.Float(string='Vehicle Odometer', required=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    notes = fields.Text(string='Notes')
    
    current_level = fields.Float(related='tanker_id.current_fuel_level', string='Current Level')
    vehicle_last_odometer = fields.Float(string='Last Odometer Reading', compute='_compute_last_odometer')
    
    @api.depends('vehicle_id')
    def _compute_last_odometer(self):
        for wizard in self:
            if wizard.vehicle_id:
                last_log = self.env['simply.fleet.fuel.log'].search([
                    ('vehicle_id', '=', wizard.vehicle_id.id),
                    ('odometer', '!=', False)
                ], order='datetime desc, id desc', limit=1)
                
                if last_log:
                    wizard.vehicle_last_odometer = last_log.odometer
                else:
                    wizard.vehicle_last_odometer = wizard.vehicle_id.initial_odometer or 0.0
            else:
                wizard.vehicle_last_odometer = 0.0
    
    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        if self.vehicle_id:
            self.odometer = self.vehicle_last_odometer
    
    def action_dispense(self):
        """Perform the dispensing operation"""
        self.ensure_one()
        
        # Check fuel level
        if self.quantity > self.current_level:
            raise UserError(f"Not enough fuel in tanker. Current level: {self.current_level} L")
        
        # Create dispensing log - which will also create the fuel log
        self.env['simply.fleet.tanker.dispensing'].create({
            'tanker_id': self.tanker_id.id,
            'vehicle_id': self.vehicle_id.id,
            'date': self.date,
            'quantity': self.quantity,
            'odometer': self.odometer,
            'notes': self.notes
        })
        
        return {
            'type': 'ir.actions.act_window_close'
        }