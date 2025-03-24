from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class UniformAssignmentLine(models.Model):
    _name = 'hr.uniform.assignment.line'
    _description = 'Uniform Assignment Line'
    
    name = fields.Char('Reference', readonly=True, default='New')
    assignment_id = fields.Many2one('uniform.assignment', string='Assignment', ondelete='cascade')
    employee_id = fields.Many2one(related='assignment_id.employee_id', string='Employee', store=True)
    item_id = fields.Many2one('uniform.item', string='Uniform Item', required=True, tracking=True)
    type_id = fields.Many2one(related='item_id.type_id', string='Uniform Type', store=True)
    category = fields.Selection(related='item_id.category', string='Category', store=True)
    size_id = fields.Many2one('uniform.size', string='Size', required=True, tracking=True)
    assignment_date = fields.Date('Assignment Date', default=fields.Date.today, required=True, tracking=True)
    return_date = fields.Date('Return Date', tracking=True)
    quantity = fields.Integer('Quantity', default=1, required=True)
    state = fields.Selection(related='assignment_id.state', string='Status', store=True)


class UniformAssignment(models.Model):
    _name = 'uniform.assignment'
    _description = 'Uniform Assignment'
    _order = 'assignment_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Reference', readonly=True, default='New')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    uniform_line_ids = fields.One2many('hr.uniform.assignment.line', 'assignment_id', string='Uniform Lines')
    item_id = fields.Many2one('uniform.item', string='Uniform Item', tracking=True)
    type_id = fields.Many2one(related='item_id.type_id', string='Uniform Type', store=True)
    category = fields.Selection(related='item_id.category', string='Category', store=True)
    size_id = fields.Many2one('uniform.size', string='Size', tracking=True)
    assignment_date = fields.Date('Assignment Date', default=fields.Date.today, required=True, tracking=True)
    return_date = fields.Date('Return Date', tracking=True)
    quantity = fields.Integer('Quantity', default=1)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('partially_returned', 'Partially Returned'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    notes = fields.Text('Notes')
    
    # For returns tracking
    return_ids = fields.One2many('uniform.return', 'assignment_id', string='Returns')
    returned_qty = fields.Integer(compute='_compute_returned_qty', string='Returned Quantity', store=True)
    
    @api.depends('return_ids.quantity')
    def _compute_returned_qty(self):
        for record in self:
            record.returned_qty = sum(return_ids.quantity for return_ids in record.return_ids)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('uniform.assignment') or 'New'
        return super(UniformAssignment, self).create(vals)
    
    def action_assign(self):
        for record in self:
            if record.state == 'draft':
                # Process uniform lines
                for line in record.uniform_line_ids:
                    # Check if item is available in stock
                    if line.item_id.qty_available < line.quantity:
                        raise ValidationError(_('Not enough quantity available for %s') % line.item_id.name)
                    
                    # Update stock
                    line.item_id.qty_available -= line.quantity
                
                record.state = 'assigned'
    
    def action_return(self):
        self.ensure_one()
        return {
            'name': _('Return Uniform'),
            'type': 'ir.actions.act_window',
            'res_model': 'uniform.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_assignment_id': self.id,
                       'default_max_quantity': self.quantity - self.returned_qty},
        }
    
    @api.constrains('returned_qty', 'quantity')
    def _check_returned_qty(self):
        for record in self:
            if record.returned_qty > record.quantity:
                raise ValidationError(_('Returned quantity cannot exceed assigned quantity'))
            
            # Update state based on returned quantity
            if record.returned_qty == 0:
                if record.state not in ['draft', 'cancelled']:
                    record.state = 'assigned'
            elif record.returned_qty < record.quantity:
                record.state = 'partially_returned'
            else:  # fully returned
                record.state = 'returned'
    
    def action_cancel(self):
        for record in self:
            if record.state not in ['returned']:
                record.state = 'cancelled'
                # Return items to stock if they've been assigned
                if record.state == 'assigned':
                    # Process all lines
                    for line in record.uniform_line_ids:
                        line.item_id.qty_available += line.quantity
