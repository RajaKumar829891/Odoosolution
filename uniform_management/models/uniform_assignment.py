from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class UniformAssignment(models.Model):
    _name = 'uniform.assignment'
    _description = 'Uniform Assignment'
    _order = 'assignment_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Reference', readonly=True, default='New')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    item_id = fields.Many2one('uniform.item', string='Uniform Item', required=True, tracking=True)
    type_id = fields.Many2one(related='item_id.type_id', string='Uniform Type', store=True)
    category = fields.Selection(related='item_id.category', string='Category', store=True)
    size_id = fields.Many2one('uniform.size', string='Size', required=True, tracking=True)
    assignment_date = fields.Date('Assignment Date', default=fields.Date.today, required=True, tracking=True)
    expected_return_date = fields.Date('Expected Return Date', compute='_compute_expected_return_date', store=True)
    quantity = fields.Integer('Quantity', default=1, required=True)
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
    
    @api.depends('item_id', 'item_id.replacement_period', 'assignment_date')
    def _compute_expected_return_date(self):
        for record in self:
            if record.assignment_date and record.item_id.replacement_period:
                record.expected_return_date = record.assignment_date + timedelta(days=record.item_id.replacement_period * 30)
            else:
                record.expected_return_date = False
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('uniform.assignment') or 'New'
        return super(UniformAssignment, self).create(vals)
    
    def action_assign(self):
        for record in self:
            if record.state == 'draft':
                # Check if item is available in stock
                if record.item_id.qty_available < record.quantity:
                    raise ValidationError(_('Not enough quantity available for %s') % record.item_id.name)
                
                # Update stock
                record.item_id.qty_available -= record.quantity
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
                    record.item_id.qty_available += (record.quantity - record.returned_qty)
