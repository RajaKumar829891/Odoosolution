from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
class MassUniformAssignment(models.TransientModel):
    _name = 'mass.uniform.assignment'
    _description = 'Mass Uniform Assignment'
    
    uniform_item_id = fields.Many2one('product.template', string='Uniform Item', 
                                     domain=[('is_uniform', '=', True)], required=True)
    uniform_type = fields.Selection(related='uniform_item_id.uniform_type', readonly=True)
    product_variant_id = fields.Many2one('product.product', string='Variant', required=True,
                                        domain="[('product_tmpl_id', '=', uniform_item_id)]")
    quantity = fields.Integer(string='Quantity per Employee', default=1, required=True)
    assignment_date = fields.Date(string='Assignment Date', default=fields.Date.today, required=True)
    expected_return_date = fields.Date(string='Expected Return Date')
    notes = fields.Text(string='Notes')
    
    employee_ids = fields.Many2many('hr.employee', string='Employees', required=True)
    
    @api.onchange('uniform_item_id')
    def _onchange_uniform_item(self):
        self.product_variant_id = False
    
    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero."))
    
    def action_assign(self):
        self.ensure_one()
        
        # Check if enough stock is available
        total_needed = len(self.employee_ids) * self.quantity
        available = sum(self.env['stock.quant'].search([
            ('product_id', '=', self.product_variant_id.id),
            ('location_id.usage', '=', 'internal')
        ]).mapped('quantity'))
        
        if available < total_needed:
            raise UserError(_(
                "Not enough quantity available for %s (%s). Need %s but only %s available."
            ) % (self.uniform_item_id.name, self.product_variant_id.display_name, total_needed, available))
        
        assignments = self.env['uniform.assignment']
        for employee in self.employee_ids:
            # Create assignment record
            assignment_vals = {
                'employee_id': employee.id,
                'uniform_item_id': self.uniform_item_id.id,
                'product_variant_id': self.product_variant_id.id,
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