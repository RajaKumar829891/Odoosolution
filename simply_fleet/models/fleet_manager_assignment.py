from odoo import models, fields, api

class FleetManagerAssignment(models.Model):
    _name = 'simply.fleet.manager.assignment'
    _description = 'Fleet Manager Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Reference',
        readonly=True,
        copy=False,
        default='New'
    )
    
    fleet_manager_id = fields.Many2one(
        'hr.employee',
        string='Fleet Manager',
        required=True,
        tracking=True,
        domain=[('is_fleet_manager', '=', True)],
        help='Manager responsible for vehicle groups'
    )
    
    vehicle_group_ids = fields.Many2many(
        'simply.fleet.vehicle.group',
        string='Vehicle Groups',
        required=True,
        tracking=True,
        help='Vehicle groups managed by this fleet manager'
    )
    
    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True,
        default=fields.Date.context_today
    )
    
    end_date = fields.Date(
        string='End Date',
        tracking=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notes', tracking=True)
    
    vehicle_count = fields.Integer(
        string='Total Vehicles',
        compute='_compute_vehicle_count'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('simply.fleet.manager.assignment') or 'New'
        return super().create(vals_list)

    @api.depends('vehicle_group_ids')
    def _compute_vehicle_count(self):
        for record in self:
            vehicles = self.env['simply.fleet.vehicle'].search([
                ('group_id', 'in', record.vehicle_group_ids.ids)
            ])
            record.vehicle_count = len(vehicles)

    def action_set_active(self):
        self.write({'state': 'active'})

    def action_set_expired(self):
        self.write({'state': 'expired'})

    def action_set_cancelled(self):
        self.write({'state': 'cancelled'})

    def action_view_vehicles(self):
        self.ensure_one()
        return {
            'name': 'Managed Vehicles',
            'type': 'ir.actions.act_window',
            'res_model': 'simply.fleet.vehicle',
            'view_mode': 'tree,form',
            'domain': [('group_id', 'in', self.vehicle_group_ids.ids)],
            'context': {'create': False}
        }
