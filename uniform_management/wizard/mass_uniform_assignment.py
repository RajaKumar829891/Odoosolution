from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class MassUniformAssignmentLine(models.TransientModel):
    _name = 'mass.uniform.assignment.line'
    _description = 'Mass Uniform Assignment Line'
    
    wizard_id = fields.Many2one('mass.uniform.assignment', string='Wizard')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    size_id = fields.Many2one('uniform.size', string='Size')
    quantity = fields.Integer('Quantity', default=1)
    has_size = fields.Boolean('Has Size', help="Indicates if a size was automatically determined")
    
    # Additional fields to help in display
    department_id = fields.Many2one(related='employee_id.department_id', string='Department')
    job_id = fields.Many2one(related='employee_id.job_id', string='Job Position')

class MassUniformAssignment(models.TransientModel):
    _name = 'mass.uniform.assignment'
    _description = 'Mass Uniform Assignment'
    
    # Selection criteria
    department_id = fields.Many2one('hr.department', string='Department')
    job_id = fields.Many2one('hr.job', string='Job Position')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    
    # Uniform details
    item_id = fields.Many2one('uniform.item', string='Uniform Item', required=True)
    assignment_date = fields.Date('Assignment Date', default=fields.Date.today, required=True)
    quantity = fields.Integer('Quantity per Employee', default=1, required=True)
    notes = fields.Text('Notes')
    
    # Size settings
    auto_size = fields.Boolean('Use Employee Size Settings', 
                             help="Automatically use size preferences from employee profiles")
    size_id = fields.Many2one('uniform.size', string='Size (if not using auto size)')
    
    # Preview
    preview_line_ids = fields.One2many('mass.uniform.assignment.line', 'wizard_id', string='Preview')
    employee_count = fields.Integer(compute='_compute_employee_count', string='Number of Employees')
    
    @api.depends('employee_ids', 'department_id', 'job_id')
    def _compute_employee_count(self):
        for wizard in self:
            domain = []
            if wizard.employee_ids:
                domain = [('id', 'in', wizard.employee_ids.ids)]
            else:
                if wizard.department_id:
                    domain.append(('department_id', '=', wizard.department_id.id))
                if wizard.job_id:
                    domain.append(('job_id', '=', wizard.job_id.id))
            
            wizard.employee_count = len(self.env['hr.employee'].search(domain))
    
    @api.onchange('department_id', 'job_id', 'employee_ids', 'item_id', 'auto_size')
    def _onchange_generate_preview(self):
        self.preview_line_ids = [(5, 0, 0)]  # Clear previous preview
        
        if not self.item_id:
            return
            
        # Get employees based on criteria
        domain = []
        if self.employee_ids:
            domain = [('id', 'in', self.employee_ids.ids)]
        else:
            if self.department_id:
                domain.append(('department_id', '=', self.department_id.id))
            if self.job_id:
                domain.append(('job_id', '=', self.job_id.id))
        
        employees = self.env['hr.employee'].search(domain)
        
        # Generate preview lines
        preview_lines = []
        for employee in employees:
            size_id = False
            
            # Try to determine size if auto_size is enabled
            if self.auto_size:
                if self.item_id.category == 'tshirt' and employee.tshirt_size_id:
                    size_id = employee.tshirt_size_id.id
                elif self.item_id.category == 'pants' and employee.pants_size_id:
                    size_id = employee.pants_size_id.id
                elif self.item_id.category == 'shoes' and employee.shoe_size_id:
                    size_id = employee.shoe_size_id.id
            else:
                size_id = self.size_id.id
                
            preview_lines.append((0, 0, {
                'employee_id': employee.id,
                'size_id': size_id,
                'quantity': self.quantity,
                'has_size': bool(size_id),
            }))
            
        self.preview_line_ids = preview_lines
    
    def action_assign(self):
        # Check if we have sizes for all employees
        missing_sizes = self.preview_line_ids.filtered(lambda l: not l.size_id)
        if missing_sizes:
            missing_employees = missing_sizes.mapped('employee_id.name')
            raise ValidationError(_('Missing sizes for employees: %s') % ', '.join(missing_employees))
            
        # Check stock availability
        total_quantity = sum(self.preview_line_ids.mapped('quantity'))
        if self.item_id.qty_available < total_quantity:
            raise ValidationError(_('Not enough stock available. Need %s but only %s available.') % 
                               (total_quantity, self.item_id.qty_available))
                               
        # Create assignment records
        assignments = []
        for line in self.preview_line_ids:
            vals = {
                'employee_id': line.employee_id.id,
                'item_id': self.item_id.id,
                'size_id': line.size_id.id,
                'quantity': line.quantity,
                'assignment_date': self.assignment_date,
                'notes': self.notes,
                'state': 'assigned',  # Auto-confirm assignments
            }
            assignments.append(self.env['uniform.assignment'].create(vals))
            
        # Update stock
        self.item_id.qty_available -= total_quantity
        
        # Show the created assignments
        action = {
            'name': _('Uniform Assignments'),
            'type': 'ir.actions.act_window',
            'res_model': 'uniform.assignment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', [a.id for a in assignments])],
        }
        return action
