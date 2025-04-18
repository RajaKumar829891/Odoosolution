from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MassUniformAssignment(models.TransientModel):
    _name = 'mass.uniform.assignment'
    _description = 'Mass Uniform Assignment'
    
    uniform_item_id = fields.Many2one('product.template', string='Uniform Item', 
                                     domain=[('is_uniform', '=', True)], required=True)
    uniform_type = fields.Selection(related='uniform_item_id.uniform_type', readonly=True)
    size_id = fields.Many2one('uniform.item.size', string='Size', required=True,
                             domain="[('product_id', '=', uniform_item_id)]")
    quantity = fields.Integer(string='Quantity per Employee', default=1, required=True)
    assignment_date = fields.Date(string='Assignment Date', default=fields.Date.today, required=True)
    expected_return_date = fields.Date(string='Expected Return Date')
    notes = fields.Text(string='Notes')
    
    employee_ids = fields.Many2many('hr.employee', string='Employees', required=True)
    
    @api.onchange('uniform_item_id')
    def _onchange_uniform_item(self):
        self.size_id = False
    
    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero."))
    
    def action_assign(self):
        self.ensure_one()
        
        # Check if enough stock is available
        total_needed = len(self.employee_ids) * self.quantity
        if self.size_id.quantity < total_needed:
            raise UserError(_(
                "Not enough quantity available for %s in size %s. Need %s but only %s available."
            ) % (self.uniform_item_id.name, self.size_id.name, total_needed, self.size_id.quantity))
        
        assignments = self.env['uniform.assignment']
        for employee in self.employee_ids:
            assignment_vals = {
                'employee_id': employee.id,
                'uniform_item_id': self.uniform_item_id.id,
                'size_id': self.size_id.id,
                'quantity': self.quantity,
                'assignment_date': self.assignment_date,
                'expected_return_date': self.expected_return_date,
                'notes': self.notes,
                'state': 'draft',
            }
            
            assignment = self.env['uniform.assignment'].create(assignment_vals)
            assignments += assignment
            
        # Assign all created records
        assignments.action_assign()
        
        # Show the created assignments
        action = {
            'name': _('Assigned Uniforms'),
            'type': 'ir.actions.act_window',
            'res_model': 'uniform.assignment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', assignments.ids)],
            'target': 'current',
        }
        
        return action
