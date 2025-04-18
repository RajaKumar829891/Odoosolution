from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class UniformReturn(models.Model):
    _name = 'uniform.return'
    _description = 'Uniform Return'
    _order = 'return_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Reference', required=True, copy=False, 
                      readonly=True, default=lambda self: _('New'))
    assignment_id = fields.Many2one('uniform.assignment', string='Assignment Reference', 
                                   required=True, tracking=True)
    line_id = fields.Many2one('uniform.assignment.line', string='Assignment Line',
                            domain="[('assignment_id', '=', assignment_id)]")
    employee_id = fields.Many2one(related='assignment_id.employee_id', store=True, readonly=True)
    
    # Fields for backward compatibility
    uniform_item_id = fields.Many2one(related='assignment_id.uniform_item_id', store=True, readonly=True)
    size_id = fields.Many2one(related='assignment_id.size_id', store=True, readonly=True)
    assigned_quantity = fields.Integer(related='assignment_id.quantity', string='Assigned Quantity')
    
    quantity = fields.Integer(string='Return Quantity', default=1, required=True, tracking=True)
    return_date = fields.Date(string='Return Date', default=fields.Date.today, required=True, tracking=True)
    condition = fields.Selection([
        ('good', 'Good'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost')
    ], string='Condition', default='good', required=True, tracking=True)
    reusable = fields.Boolean(string='Reusable', default=True, 
                             help="Whether the item can be reused and returned to inventory")
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    @api.onchange('condition')
    def _onchange_condition(self):
        if self.condition in ['damaged', 'lost']:
            self.reusable = False
        else:
            self.reusable = True
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('uniform.return') or _('New')
        
        # Create the record first
        result = super(UniformReturn, self).create(vals)
        
        # Update inventory only for reusable items
        if result.reusable:
            if result.line_id:
                result.line_id.size_id.quantity += result.quantity
            elif result.size_id:
                result.size_id.quantity += result.quantity
            
        return result
    
    @api.constrains('quantity', 'assignment_id', 'line_id')
    def _check_return_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Return quantity must be greater than zero."))
            
            # Check for line items or direct assignment
            if record.line_id:
                # Calculate how many items have already been returned for this line
                already_returned = sum(self.env['uniform.return'].search([
                    ('assignment_id', '=', record.assignment_id.id),
                    ('line_id', '=', record.line_id.id),
                    ('id', '!=', record.id)
                ]).mapped('quantity') or [0])
                
                if record.quantity + already_returned > record.line_id.quantity:
                    raise ValidationError(_("You cannot return more items than were assigned."))
            else:
                # Calculate how many items have already been returned
                already_returned = sum(self.env['uniform.return'].search([
                    ('assignment_id', '=', record.assignment_id.id),
                    ('id', '!=', record.id)
                ]).mapped('quantity') or [0])
                
                if record.quantity + already_returned > record.assigned_quantity:
                    raise ValidationError(_("You cannot return more items than were assigned."))
