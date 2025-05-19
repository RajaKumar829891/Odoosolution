from odoo import api, fields, models, _


class FleetBookingStatus(models.Model):
    _name = 'fleet.booking.status'
    _description = 'Fleet Booking Status'
    _order = 'sequence'

    name = fields.Char(string='Status Name', required=True, translate=True)
    code = fields.Char(string='Status Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description')
    color = fields.Integer(string='Color Index', default=0)
    fold = fields.Boolean(string='Folded in Kanban', default=False)
    
    # Used to track which statuses can transition to which others
    allowed_next_status_ids = fields.Many2many(
        'fleet.booking.status', 'fleet_booking_status_next_rel', 
        'status_id', 'next_status_id', string='Allowed Next Statuses')
        
    is_initial = fields.Boolean(string='Is Initial Status', default=False)
    is_final = fields.Boolean(string='Is Final Status', default=False)
    
    # Map to the state field in fleet.booking model
    state_mapping = fields.Selection([
        ('enquiry', 'Enquiry'),
        ('quotation', 'Quotation'),
        ('followup', 'Follow Up'),
        ('confirmed_pending', 'Confirmed (Lost/Cancelled)'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('feedback', 'Feedback'),
    ], string='State Mapping', required=True)
    
    # System flags for special statuses
    is_cancelled = fields.Boolean(string='Is Cancelled Status', default=False)
    is_completed = fields.Boolean(string='Is Completed Status', default=False)
    is_quotation = fields.Boolean(string='Is Quotation Status', default=False)
    
    requires_payment = fields.Boolean(string='Requires Payment', default=False)
    requires_driver = fields.Boolean(string='Requires Driver Assignment', default=False)
    requires_feedback = fields.Boolean(string='Requires Feedback', default=False)
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Status code must be unique!'),
    ]


class FleetBookingStatusChange(models.Model):
    _name = 'fleet.booking.status.change'
    _description = 'Fleet Booking Status Change History'
    _order = 'change_date desc'

    booking_id = fields.Many2one('fleet.booking', string='Booking', required=True, ondelete='cascade')
    old_status_id = fields.Many2one('fleet.booking.status', string='From Status')
    new_status_id = fields.Many2one('fleet.booking.status', string='To Status', required=True)
    change_date = fields.Datetime(string='Change Date', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Changed By', default=lambda self: self.env.user)
    note = fields.Text(string='Note')