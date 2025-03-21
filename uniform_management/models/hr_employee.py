from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    # Uniform assignment information
    uniform_assignment_ids = fields.One2many('uniform.assignment', 'employee_id', string='Uniform Assignments')
    uniform_assignment_count = fields.Integer(compute='_compute_uniform_counts', string='Assigned Uniforms')
    uniform_active_count = fields.Integer(compute='_compute_uniform_counts', string='Active Uniforms')
    
    # T-shirt size
    tshirt_size_id = fields.Many2one('uniform.size', string='T-Shirt Size', 
                                   domain=[('size_type', '=', 'letter')])
    
    # Pants size
    pants_size_id = fields.Many2one('uniform.size', string='Pants Size',
                                  domain=[('size_type', '=', 'numeric')])
    
    # Shoe size
    shoe_size_id = fields.Many2one('uniform.size', string='Shoe Size',
                                 domain=[('size_type', '=', 'shoe')])
    
    # Belt size (waist measurement)
    belt_size = fields.Float('Belt Size (cm)')
    
    # Last uniform issue date
    last_uniform_date = fields.Date(compute='_compute_last_uniform_date', string='Last Uniform Issue Date', store=True)
    
    @api.depends('uniform_assignment_ids', 'uniform_assignment_ids.state')
    def _compute_uniform_counts(self):
        for employee in self:
            employee.uniform_assignment_count = len(employee.uniform_assignment_ids)
            employee.uniform_active_count = len(employee.uniform_assignment_ids.filtered(
                lambda a: a.state in ['assigned', 'partially_returned']))
    
    @api.depends('uniform_assignment_ids', 'uniform_assignment_ids.assignment_date')
    def _compute_last_uniform_date(self):
        for employee in self:
            assignments = employee.uniform_assignment_ids.filtered(lambda a: a.state != 'cancelled')
            if assignments:
                employee.last_uniform_date = max(assignments.mapped('assignment_date'))
            else:
                employee.last_uniform_date = False
    
    def action_view_uniforms(self):
        self.ensure_one()
        return {
            'name': 'Uniforms',
            'view_mode': 'tree,form',
            'res_model': 'uniform.assignment',
            'domain': [('employee_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_employee_id': self.id},
        }
    
    def action_assign_uniform(self):
        self.ensure_one()
        return {
            'name': 'Assign Uniform',
            'view_mode': 'form',
            'res_model': 'uniform.assignment',
            'type': 'ir.actions.act_window',
            'context': {'default_employee_id': self.id},
            'target': 'new',
        }
