from odoo import models, fields, api

class VehicleImage(models.Model):
    _name = 'simply.fleet.vehicle.image'
    _description = 'Vehicle Images'
    _order = 'sequence, id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Title', required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    image = fields.Binary(string='Image', required=True, attachment=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    
    vehicle_id = fields.Many2one(
        'simply.fleet.vehicle',
        string='Vehicle',
        required=True,
        tracking=True,
        ondelete='cascade'
    )
    
    vehicle_ref = fields.Char(
        related='vehicle_id.ref',
        string='Vehicle Reference',
        store=True,
        readonly=True
    )
    
    image_type = fields.Selection([
        ('exterior', 'Exterior'),
        ('interior', 'Interior'),
        ('damage', 'Damage'),
        ('repair', 'Repair'),
        ('other', 'Other')
    ], string='Image Type', required=True, default='exterior', tracking=True)
    
    capture_date = fields.Date(
        string='Capture Date',
        default=fields.Date.context_today,
        tracking=True
    )
    
    notes = fields.Text(string='Notes', tracking=True)

# Add the following to the existing Vehicle class
class Vehicle(models.Model):
    _inherit = 'simply.fleet.vehicle'
    
    image_count = fields.Integer(
        string='Images',
        compute='_compute_image_count'
    )
    
    def _compute_image_count(self):
        for record in self:
            record.image_count = self.env['simply.fleet.vehicle.image'].search_count([
                ('vehicle_id', '=', record.id)
            ])
    
    def action_view_images(self):
        self.ensure_one()
        return {
            'name': 'Vehicle Images',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'res_model': 'simply.fleet.vehicle.image',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
