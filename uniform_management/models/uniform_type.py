from odoo import models, fields

class UniformType(models.Model):
    _name = 'uniform.type'
    _description = 'Uniform Type'
    _order = 'name'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)
    
    # Department associations
    department_ids = fields.Many2many('hr.department', string='Applicable Departments',
                                    help="Departments where this uniform type is used")
    
    # Job position associations
    job_position_ids = fields.Many2many('hr.job', string='Applicable Job Positions',
                                      help="Job positions where this uniform type is used")
    
    # Related items
    item_ids = fields.One2many('uniform.item', 'type_id', string='Uniform Items')
    item_count = fields.Integer(compute='_compute_item_count', string='Item Count')
    
    def _compute_item_count(self):
        for uniform_type in self:
            uniform_type.item_count = len(uniform_type.item_ids)
