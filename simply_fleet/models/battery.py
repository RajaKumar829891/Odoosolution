from odoo import models, fields, api
from datetime import datetime

class VehicleBattery(models.Model):
    _name = 'simply.fleet.battery'
    _description = 'Vehicle Battery Information'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'installation_date desc'

    name = fields.Char(string='Battery Name', required=True, tracking=True)
    ref = fields.Char(string='Reference', readonly=True, copy=False)
    vehicle_id = fields.Many2one(
        'simply.fleet.vehicle',
        string='Vehicle',
        required=True,
        tracking=True
    )
    brand = fields.Char(string='Brand', tracking=True)
    model = fields.Char(string='Model', tracking=True)
    capacity = fields.Float(
        string='Capacity (Ah)',
        tracking=True,
        help='Battery capacity in Ampere-hours'
    )
    voltage = fields.Float(
        string='Voltage (V)',
        tracking=True,
        help='Battery voltage in Volts'
    )
    installation_date = fields.Date(
        string='Installation Date',
        required=True,
        tracking=True,
        default=fields.Date.today
    )
    expiry_date = fields.Date(
        string='Expected Expiry Date',
        tracking=True,
        help='Expected date when the battery should be replaced'
    )
    warranty_end_date = fields.Date(
        string='Warranty End Date',
        tracking=True
    )
    state = fields.Selection([
        ('new', 'New'),
        ('in_use', 'In Use'),
        ('degraded', 'Degraded'),
        ('replaced', 'Replaced')
    ], string='Status', default='new', tracking=True)
    health_percentage = fields.Float(
        string='Health Percentage',
        tracking=True,
        help='Current battery health percentage'
    )
    last_inspection_date = fields.Date(
        string='Last Inspection Date',
        tracking=True
    )
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)

    maintenance_history_ids = fields.One2many(
        'simply.fleet.battery.maintenance',
        'battery_id',
        string='Maintenance History'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('ref'):
                vals['ref'] = self.env['ir.sequence'].next_by_code('simply.fleet.battery')
        return super().create(vals_list)

    def action_mark_degraded(self):
        self.ensure_one()
        self.write({'state': 'degraded'})

    def action_mark_replaced(self):
        self.ensure_one()
        self.write({
            'state': 'replaced',
            'active': False,
            'notes': f'{self.notes or ""}\nReplaced on: {datetime.now().date()}'
        })


class VehicleBatteryMaintenance(models.Model):
    _name = 'simply.fleet.battery.maintenance'
    _description = 'Battery Maintenance Record'
    _order = 'date desc'

    battery_id = fields.Many2one(
        'simply.fleet.battery',
        string='Battery',
        required=True
    )
    date = fields.Date(
        string='Maintenance Date',
        required=True,
        default=fields.Date.today
    )
    maintenance_type = fields.Selection([
        ('inspection', 'Regular Inspection'),
        ('cleaning', 'Cleaning'),
        ('water_level', 'Water Level Check'),
        ('terminal_check', 'Terminal Check'),
        ('voltage_check', 'Voltage Check'),
        ('other', 'Other')
    ], string='Maintenance Type', required=True)
    voltage_reading = fields.Float(string='Voltage Reading (V)')
    performed_by = fields.Many2one('hr.employee', string='Performed By')
    notes = fields.Text(string='Notes')
    next_maintenance_date = fields.Date(string='Next Maintenance Due')
