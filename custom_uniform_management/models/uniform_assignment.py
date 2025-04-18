from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class UniformAssignmentLine(models.Model):
    _name = 'uniform.assignment.line'
    _description = 'Uniform Assignment Line'
    
    assignment_id = fields.Many2one('uniform.assignment', string='Assignment', required=True, ondelete='cascade')
    item_id = fields.Many2one('product.template', string='Uniform Item', required=True, 
                             domain=[('is_uniform', '=', True)])
    size_id = fields.Many2one('uniform.item.size', string='Size', required=True,
                             domain="[('product_id', '=', item_id)]")
    quantity = fields.Integer(string='Quantity', default=1, required=True)
    assignment_date = fields.Date(string='Assignment Date', default=fields.Date.today, required=True)
    return_date = fields.Date(string='Return Date')
    
    @api.onchange('item_id')
    def _onchange_item_id(self):
        self.size_id = False

class UniformAssignment(models.Model):
    _name = 'uniform.assignment'
    _description = 'Uniform Assignment'
    _order = 'assignment_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Reference', required=True, copy=False, 
                      readonly=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    
    # For backward compatibility with the view
    uniform_item_id = fields.Many2one('product.template', string='Uniform Item', domain=[('is_uniform', '=', True)])
    uniform_type = fields.Selection(related='uniform_item_id.uniform_type', readonly=True)
    size_id = fields.Many2one('uniform.item.size', string='Size', domain="[('product_id', '=', uniform_item_id)]")
    quantity = fields.Integer(string='Quantity', default=1)
    
    # New fields for line items
    uniform_line_ids = fields.One2many('uniform.assignment.line', 'assignment_id', string='Uniform Items')
    
    assignment_date = fields.Date(string='Assignment Date', default=fields.Date.today, required=True, tracking=True)
    expected_return_date = fields.Date(string='Return Date', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('partially_returned', 'Partially Returned'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    return_ids = fields.One2many('uniform.return', 'assignment_id', string='Returns')
    returned_quantity = fields.Integer(string='Returned Quantity', compute='_compute_returned_quantity', store=True)
    
    # Alias field for compatibility with the view
    returned_qty = fields.Integer(related='returned_quantity', string='Returned Qty')
    
    @api.depends('return_ids.quantity')
    def _compute_returned_quantity(self):
        for record in self:
            record.returned_quantity = sum(record.return_ids.mapped('quantity') or [0])
            if record.returned_quantity == 0:
                if record.state == 'assigned':
                    pass  # Keep current state
            elif record.returned_quantity < record.quantity:
                record.state = 'partially_returned'
            elif record.returned_quantity >= record.quantity:
                record.state = 'returned'
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('uniform.assignment') or _('New')
        return super(UniformAssignment, self).create(vals)
    
    @api.constrains('quantity', 'size_id')
    def _check_quantity_available(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero."))
            
            if record.state == 'draft' and record.size_id:
                available = record.size_id.quantity
                if record.quantity > available:
                    raise ValidationError(_(
                        "Not enough quantity available for %s in size %s. Only %s available."
                    ) % (record.uniform_item_id.name, record.size_id.name, available))
    
    @api.onchange('uniform_item_id')
    def _onchange_uniform_item(self):
        self.size_id = False
    
    def action_assign(self):
        for record in self:
            if record.state != 'draft':
                continue
                
            # If using line items
            if record.uniform_line_ids:
                for line in record.uniform_line_ids:
                    if line.size_id.quantity < line.quantity:
                        raise UserError(_("Not enough quantity available for %s in size %s.") % 
                                        (line.item_id.name, line.size_id.name))
                    line.size_id.quantity -= line.quantity
            # If using the old way
            elif record.size_id and record.quantity > 0:
                if record.size_id.quantity < record.quantity:
                    raise UserError(_("Not enough quantity available for %s in size %s.") % 
                                    (record.uniform_item_id.name, record.size_id.name))
                record.size_id.quantity -= record.quantity
                
            record.state = 'assigned'
    
    def action_cancel(self):
        for record in self:
            if record.state in ['draft', 'assigned', 'partially_returned']:
                # If already assigned, return to inventory
                if record.state in ['assigned', 'partially_returned']:
                    if record.uniform_line_ids:
                        for line in record.uniform_line_ids:
                            # Calculate how many to return to inventory
                            returned = sum(self.env['uniform.return'].search([
                                ('assignment_id', '=', record.id),
                                ('line_id', '=', line.id),
                                ('condition', '=', 'good')
                            ]).mapped('quantity') or [0])
                            to_return = line.quantity - returned
                            if to_return > 0:
                                line.size_id.quantity += to_return
                    elif record.size_id:
                        record.size_id.quantity += (record.quantity - record.returned_quantity)
                record.state = 'cancelled'
