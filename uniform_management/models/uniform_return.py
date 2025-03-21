from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class UniformReturn(models.Model):
    _name = 'uniform.return'
    _description = 'Uniform Return'
    _order = 'return_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Reference', readonly=True, default='New')
    assignment_id = fields.Many2one('uniform.assignment', string='Assignment Reference', 
                                   required=True, ondelete='cascade', tracking=True)
    employee_id = fields.Many2one(related='assignment_id.employee_id', string='Employee', store=True)
    item_id = fields.Many2one(related='assignment_id.item_id', string='Uniform Item', store=True)
    return_date = fields.Date('Return Date', default=fields.Date.today, required=True, tracking=True)
    quantity = fields.Integer('Quantity Returned', default=1, required=True)
    condition = fields.Selection([
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost'),
    ], string='Condition', required=True, default='good', tracking=True)
    reusable = fields.Boolean('Reusable', compute='_compute_reusable', store=True)
    notes = fields.Text('Notes')
    
    @api.depends('condition')
    def _compute_reusable(self):
        for record in self:
            record.reusable = record.condition in ['good', 'fair']
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('uniform.return') or 'New'
        
        record = super(UniformReturn, self).create(vals)
        
        # Update stock if the item is reusable
        if record.reusable:
            record.item_id.qty_available += record.quantity
            
        return record
    
    @api.constrains('quantity', 'assignment_id')
    def _check_return_quantity(self):
        for record in self:
            assigned_qty = record.assignment_id.quantity
            already_returned_qty = sum(self.env['uniform.return'].search([
                ('assignment_id', '=', record.assignment_id.id),
                ('id', '!=', record.id)
            ]).mapped('quantity'))
            
            if record.quantity + already_returned_qty > assigned_qty:
                raise ValidationError(_(
                    'Cannot return more than assigned. Assigned: %s, Already returned: %s, Attempting to return: %s'
                ) % (assigned_qty, already_returned_qty, record.quantity))
    
    def unlink(self):
        for record in self:
            # If removing a return record, restore stock accordingly
            if record.reusable:
                record.item_id.qty_available -= record.quantity
        return super(UniformReturn, self).unlink()

# Wizard for returning uniforms
class UniformReturnWizard(models.TransientModel):
    _name = 'uniform.return.wizard'
    _description = 'Return Uniform Wizard'
    
    assignment_id = fields.Many2one('uniform.assignment', string='Assignment', required=True)
    return_date = fields.Date('Return Date', default=fields.Date.today, required=True)
    quantity = fields.Integer('Quantity to Return', default=1, required=True)
    max_quantity = fields.Integer('Maximum Quantity')
    condition = fields.Selection([
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost'),
    ], string='Condition', required=True, default='good')
    notes = fields.Text('Notes')
    
    @api.constrains('quantity', 'max_quantity')
    def _check_quantity(self):
        for wizard in self:
            if wizard.quantity <= 0:
                raise ValidationError(_('Quantity must be greater than zero'))
            if wizard.quantity > wizard.max_quantity:
                raise ValidationError(_('Cannot return more than %s items') % wizard.max_quantity)
    
    def action_return(self):
        self.ensure_one()
        vals = {
            'assignment_id': self.assignment_id.id,
            'return_date': self.return_date,
            'quantity': self.quantity,
            'condition': self.condition,
            'notes': self.notes,
        }
        self.env['uniform.return'].create(vals)
        return {'type': 'ir.actions.act_window_close'}
