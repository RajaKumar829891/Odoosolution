from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class VehicleAsset(models.Model):
    _name = 'simply.fleet.vehicle.asset'
    _description = 'Vehicle Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Asset Name', required=True, tracking=True)
    asset_type = fields.Selection([
        ('music_system', 'Music System'),
        ('gps', 'GPS Device'),
        ('camera', 'Camera'),
        ('sensor', 'Sensor'),
        ('other', 'Other')
    ], string='Asset Type', required=True, tracking=True)
    
    vehicle_id = fields.Many2one('simply.fleet.vehicle', string='Vehicle', 
                                required=True, tracking=True)
    manufacturer = fields.Char(string='Manufacturer', tracking=True)
    model = fields.Char(string='Model', tracking=True)
    serial_number = fields.Char(string='Serial Number', tracking=True)
    
    purchase_date = fields.Date(string='Purchase Date', tracking=True)
    purchase_value = fields.Float(string='Purchase Value', tracking=True)
    warranty_end_date = fields.Date(string='Warranty End Date', tracking=True)
    
    specifications = fields.Text(string='Specifications')
    notes = fields.Text(string='Notes')
    
    state = fields.Selection([
        ('active', 'Active'),
        ('maintenance', 'In Maintenance'),
        ('disposed', 'Disposed')
    ], string='Status', default='active', required=True, tracking=True)
    
    active = fields.Boolean(default=True, tracking=True)
    
    maintenance_history = fields.One2many(
        'simply.fleet.vehicle.asset.maintenance',
        'asset_id',
        string='Maintenance History'
    )

    @api.constrains('purchase_date', 'warranty_end_date')
    def _check_dates(self):
        for record in self:
            if record.purchase_date and record.warranty_end_date:
                if record.warranty_end_date < record.purchase_date:
                    raise ValidationError(_("Warranty end date cannot be before purchase date."))

    def action_set_maintenance(self):
        self.ensure_one()
        self.state = 'maintenance'

    def action_set_active(self):
        self.ensure_one()
        self.state = 'active'

    def action_set_disposed(self):
        self.ensure_one()
        self.state = 'disposed'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name', False):
                vals['name'] = self.env['ir.sequence'].next_by_code('simply.fleet.vehicle.asset')
        return super(VehicleAsset, self).create(vals_list)

class VehicleAssetMaintenance(models.Model):
    _name = 'simply.fleet.vehicle.asset.maintenance'
    _description = 'Vehicle Asset Maintenance History'
    _order = 'date desc'

    asset_id = fields.Many2one('simply.fleet.vehicle.asset', string='Asset',
                              required=True, ondelete='cascade')
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    description = fields.Text(string='Description', required=True)
    cost = fields.Float(string='Cost')
    performed_by = fields.Char(string='Performed By')

class Vehicle(models.Model):
    _inherit = 'simply.fleet.vehicle'

    asset_ids = fields.One2many('simply.fleet.vehicle.asset', 'vehicle_id', 
                               string='Assets')
    asset_count = fields.Integer(string='Asset Count', 
                               compute='_compute_asset_count')

    def _compute_asset_count(self):
        for record in self:
            record.asset_count = len(record.asset_ids)

    def action_view_assets(self):
        self.ensure_one()
        return {
            'name': _('Assets'),
            'view_mode': 'tree,form',
            'res_model': 'simply.fleet.vehicle.asset',
            'type': 'ir.actions.act_window',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {
                'default_vehicle_id': self.id,
            }
        }
