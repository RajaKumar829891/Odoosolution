# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class SimplyFleetCamera(models.Model):
    _name = 'simply.fleet.camera'
    _description = 'Fleet Camera'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Referencing
    name = fields.Char(string='Camera Name', required=True, tracking=True)
    ref = fields.Char(string='Reference', copy=False, readonly=True, 
                      default=lambda self: self.env['ir.sequence'].next_by_code('simply.fleet.camera') or '/')
    
    # Vehicle Association
    vehicle_id = fields.Many2one('simply.fleet.vehicle', string='Vehicle', tracking=True)
    
    # Basic Details
    camera_type = fields.Selection([
        ('dashcam', 'Dashcam'),
        ('interior', 'Interior Camera'),
        ('exterior', 'Exterior Camera'),
        ('360_degree', '360 Degree Camera'),
        ('thermal', 'Thermal Camera'),
        ('other', 'Other')
    ], string='Camera Type', tracking=True)
    brand = fields.Char(string='Brand', tracking=True)
    model = fields.Char(string='Model', tracking=True)
    serial_number = fields.Char(string='Serial Number', tracking=True)
    
    # Installation and Maintenance
    installation_date = fields.Date(string='Installation Date', tracking=True)
    last_maintenance_date = fields.Date(string='Last Maintenance Date', tracking=True)
    next_maintenance_date = fields.Date(string='Next Maintenance Date', tracking=True)
    
    # Technical Details
    resolution = fields.Char(string='Resolution', help='e.g. 1080p, 4K')
    storage_capacity = fields.Char(string='Storage Capacity', help='e.g. 128GB')
    recording_mode = fields.Selection([
        ('continuous', 'Continuous'),
        ('event', 'Event-based'),
        ('scheduled', 'Scheduled')
    ], string='Recording Mode')
    night_vision_range = fields.Char(string='Night Vision Range', help='e.g. 30m')
    connectivity_type = fields.Selection([
        ('wifi', 'WiFi'),
        ('cellular', 'Cellular'),
        ('bluetooth', 'Bluetooth'),
        ('ethernet', 'Ethernet'),
        ('other', 'Other')
    ], string='Connectivity Type')
    power_source = fields.Selection([
        ('vehicle_power', 'Vehicle Power'),
        ('battery', 'Battery'),
        ('solar', 'Solar'),
        ('other', 'Other')
    ], string='Power Source')
    
    # SIM and Networking Details
    sim_name = fields.Char(string='SIM Name', tracking=True)
    sim_number = fields.Char(string='SIM Number', tracking=True)
    mobile_number = fields.Char(string='Mobile Number', tracking=True)
    network_provider = fields.Char(string='Network Provider', tracking=True)
    sim_validity_start_date = fields.Date(string='SIM Validity Start Date', tracking=True)
    sim_validity_end_date = fields.Date(string='SIM Validity End Date', tracking=True)
    sim_status = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended')
    ], string='SIM Status', compute='_compute_sim_status', store=True)
    
    # Status and Tracking
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('damaged', 'Damaged')
    ], string='Camera Status', default='active', tracking=True)
    
    # Additional Information
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    
    @api.depends('sim_validity_start_date', 'sim_validity_end_date')
    def _compute_sim_status(self):
        today = fields.Date.today()
        for record in self:
            if not record.sim_validity_end_date:
                record.sim_status = 'active'
            elif record.sim_validity_end_date < today:
                record.sim_status = 'expired'
            elif record.sim_validity_start_date and record.sim_validity_start_date > today:
                record.sim_status = 'suspended'
            else:
                record.sim_status = 'active'
    
    @api.constrains('sim_validity_start_date', 'sim_validity_end_date')
    def _check_sim_validity_dates(self):
        for record in self:
            if record.sim_validity_start_date and record.sim_validity_end_date:
                if record.sim_validity_start_date > record.sim_validity_end_date:
                    raise ValidationError("SIM validity start date cannot be later than end date.")
    
    def action_view_vehicle(self):
        if self.vehicle_id:
            return {
                'name': 'Vehicle Details',
                'type': 'ir.actions.act_window',
                'res_model': 'simply.fleet.vehicle',
                'view_mode': 'form',
                'res_id': self.vehicle_id.id,
                'target': 'current',
            }
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('ref'):
                vals['ref'] = self.env['ir.sequence'].next_by_code('simply.fleet.camera') or '/'
        return super().create(vals_list)
    
    def _compute_next_maintenance(self):
        """
        Compute and set the next maintenance date based on last maintenance date.
        This is an example implementation and can be customized as per specific requirements.
        """
        for record in self:
            if record.last_maintenance_date:
                record.next_maintenance_date = record.last_maintenance_date + relativedelta(months=6)
