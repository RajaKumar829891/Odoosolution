from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    uniform_assignment_ids = fields.One2many('uniform.assignment', 'employee_id', string='Uniform Assignments')
    uniform_return_ids = fields.One2many('uniform.return', 'employee_id', string='Uniform Returns')
    
    uniform_assignment_count = fields.Integer(compute='_compute_uniform_counts', string='Assigned Uniforms')
    uniform_return_count = fields.Integer(compute='_compute_uniform_counts', string='Returned Uniforms')
    
    @api.depends('uniform_assignment_ids', 'uniform_return_ids')
    def _compute_uniform_counts(self):
        for employee in self:
            employee.uniform_assignment_count = len(employee.uniform_assignment_ids)
            employee.uniform_return_count = len(employee.uniform_return_ids)
