from odoo import models, fields, api

class FleetTyre(models.Model):
    _name = 'simply.fleet.tyre'
    _description = 'Vehicle Tyre Information'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'installation_date desc'

    name = fields.Char(
        string='Tyre ID',
        required=True,
        tracking=True
    )
    vehicle_id = fields.Many2one(
        'simply.fleet.vehicle',
        string='Vehicle',
        required=True,
        tracking=True
    )
    brand = fields.Char(
        string='Brand',
        tracking=True
    )
    model = fields.Char(
        string='Model',
        tracking=True
    )
    size = fields.Char(
        string='Size',
        tracking=True
    )
    position = fields.Selection([
        ('front_left', 'Front Left'),
        ('front_right', 'Front Right'),
        ('rear_left', 'Rear Left'),
        ('rear_right', 'Rear Right'),
        ('spare', 'Spare')
    ], string='Position', required=True, tracking=True)
    
    installation_date = fields.Date(
        string='Installation Date',
        tracking=True
    )
    removal_date = fields.Date(
        string='Removal Date',
        tracking=True
    )
    purchase_date = fields.Date(
        string='Purchase Date',
        tracking=True
    )
    purchase_price = fields.Float(
        string='Purchase Price',
        tracking=True
    )
    supplier_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        tracking=True
    )
    initial_tread_depth = fields.Float(
        string='Initial Tread Depth (mm)',
        tracking=True
    )
    current_tread_depth = fields.Float(
        string='Current Tread Depth (mm)',
        tracking=True
    )
    state = fields.Selection([
        ('new', 'New'),
        ('in_use', 'In Use'),
        ('worn', 'Worn'),
        ('damaged', 'Damaged'),
        ('disposed', 'Disposed')
    ], string='Status', default='new', tracking=True)
    
    notes = fields.Text(
        string='Notes',
        tracking=True
    )
    active = fields.Boolean(
        default=True
    )

    @api.onchange('current_tread_depth')
    def _onchange_tread_depth(self):
        if self.current_tread_depth and self.current_tread_depth < 1.6:  # Standard minimum tread depth
            return {
                'warning': {
                    'title': 'Warning!',
                    'message': 'Tread depth is below the legal minimum! Consider replacing the tyre.'
                }
            }

    @api.onchange('installation_date')
    def _onchange_installation_date(self):
        if self.installation_date:
            self.state = 'in_use'

    @api.onchange('removal_date')
    def _onchange_removal_date(self):
        if self.removal_date:
            self.state = 'disposed'

    @api.model
    def create(self, vals):
        """Override create method to handle initial values"""
        if vals.get('initial_tread_depth') and not vals.get('current_tread_depth'):
            vals['current_tread_depth'] = vals['initial_tread_depth']
        return super(FleetTyre, self).create(vals)

    def write(self, vals):
        """Override write method to handle state changes"""
        if 'current_tread_depth' in vals:
            if vals['current_tread_depth'] < 1.6 and self.state == 'in_use':
                vals['state'] = 'worn'
        return super(FleetTyre, self).write(vals)

    def action_set_new(self):
        """Set tyre state to new"""
        self.write({'state': 'new'})

    def action_set_in_use(self):
        """Set tyre state to in use"""
        self.write({'state': 'in_use'})

    def action_set_worn(self):
        """Set tyre state to worn"""
        self.write({'state': 'worn'})

    def action_set_damaged(self):
        """Set tyre state to damaged"""
        self.write({'state': 'damaged'})

    def action_set_disposed(self):
        """Set tyre state to disposed"""
        self.write({
            'state': 'disposed',
            'removal_date': fields.Date.today(),
            'active': False
        })

    _sql_constraints = [
        ('unique_position_per_vehicle', 
         'UNIQUE(vehicle_id, position)', 
         'Only one tyre can be assigned to a position on a vehicle!')
    ]
