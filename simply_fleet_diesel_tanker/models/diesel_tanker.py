from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class SimplyFleetDieselTanker(models.Model):
    _name = 'simply.fleet.diesel.tanker'
    _description = 'Diesel Tanker'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Tanker ID', required=True, readonly=True, copy=False, default='New')
    active = fields.Boolean(default=True)
    capacity = fields.Float(string='Total Capacity (Liters)', required=True, tracking=True)
    current_fuel_level = fields.Float(string='Current Fuel Level (Liters)', required=True, tracking=True)
    state = fields.Selection([
        ('empty', 'Empty'),
        ('low', 'Low Fuel'),
        ('medium', 'Medium Fuel'),
        ('full', 'Full')
    ], string='Status', compute='_compute_state', store=True)
    
    refill_log_ids = fields.One2many('simply.fleet.tanker.refill', 'tanker_id', string='Refill Logs')
    dispensing_log_ids = fields.One2many('simply.fleet.tanker.dispensing', 'tanker_id', string='Dispensing Logs')

    color = fields.Integer(string='Color', compute='_compute_color')
    fuel_percentage = fields.Float(string='Fuel Percentage', compute='_compute_fuel_percentage', store=True)
    
    last_refill_date = fields.Datetime(string='Last Refill Date', compute='_compute_last_refill_date', store=True)
    
    # Statistics fields
    total_fuel_dispensed = fields.Float(string='Total Fuel Dispensed', compute='_compute_statistics')
    total_refills = fields.Float(string='Total Refills', compute='_compute_statistics')
    
    @api.depends('capacity', 'current_fuel_level')
    def _compute_fuel_percentage(self):
        for record in self:
            if record.capacity > 0:
                record.fuel_percentage = (record.current_fuel_level / record.capacity) * 100
            else:
                record.fuel_percentage = 0
                
    @api.depends('refill_log_ids', 'refill_log_ids.date')
    def _compute_last_refill_date(self):
        for record in self:
            last_refill = self.env['simply.fleet.tanker.refill'].search([
                ('tanker_id', '=', record.id)
            ], order='date desc', limit=1)
            
            if last_refill:
                record.last_refill_date = last_refill.date
            else:
                record.last_refill_date = False
    
    @api.depends('dispensing_log_ids', 'refill_log_ids')
    def _compute_statistics(self):
        for record in self:
            record.total_fuel_dispensed = sum(record.dispensing_log_ids.mapped('quantity'))
            record.total_refills = sum(record.refill_log_ids.mapped('quantity'))
    
    @api.depends('current_fuel_level')
    def _compute_color(self):
        for record in self:
            if record.current_fuel_level >= 800:
                record.color = 10  # Green
            elif record.current_fuel_level >= 400:
                record.color = 3   # Yellow
            else:
                record.color = 1   # Red

    @api.depends('current_fuel_level', 'capacity')
    def _compute_state(self):
        for record in self:
            if record.current_fuel_level <= 0:
                record.state = 'empty'
            elif record.current_fuel_level < 400:
                record.state = 'low'
            elif record.current_fuel_level < 800:
                record.state = 'medium'
            else:
                record.state = 'full'
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('simply.fleet.diesel.tanker') or 'New'
        return super().create(vals_list)
    
    def action_view_refill_logs(self):
        """Show all refill logs for this tanker"""
        self.ensure_one()
        action = {
            'name': 'Refill Logs',
            'type': 'ir.actions.act_window',
            'res_model': 'simply.fleet.tanker.refill',
            'view_mode': 'tree,form',
            'domain': [('tanker_id', '=', self.id)],
            'context': {'default_tanker_id': self.id}
        }
        return action
    
    def action_view_dispensing_logs(self):
        """Show all dispensing logs for this tanker"""
        self.ensure_one()
        action = {
            'name': 'Dispensing Logs',
            'type': 'ir.actions.act_window',
            'res_model': 'simply.fleet.tanker.dispensing',
            'view_mode': 'tree,form',
            'domain': [('tanker_id', '=', self.id)],
            'context': {'default_tanker_id': self.id}
        }
        return action
    
    def action_refill_tanker(self):
        """Open wizard to refill the tanker"""
        self.ensure_one()
        return {
            'name': 'Refill Tanker',
            'type': 'ir.actions.act_window',
            'res_model': 'simply.fleet.tanker.refill.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_tanker_id': self.id}
        }