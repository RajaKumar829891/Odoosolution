from odoo import models, fields, api

class UniformItem(models.Model):
    _name = 'uniform.item'
    _description = 'Uniform Item'
    _order = 'name'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    type_id = fields.Many2one('uniform.type', string='Uniform Type', required=True)
    category = fields.Selection([
        ('tshirt', 'T-Shirt'),
        ('pants', 'Pants'),
        ('shoes', 'Shoes'),
        ('belt', 'Belt'),
        ('jacket', 'Jacket'),
        ('cap', 'Cap'),
        ('other', 'Other'),
    ], string='Category', required=True)
    description = fields.Text('Description')
    image = fields.Binary('Image')
    active = fields.Boolean('Active', default=True)
    
    # Size related fields
    size_type = fields.Selection([
        ('numeric', 'Numeric (e.g., 40, 42)'),
        ('letter', 'Letter (e.g., S, M, L)'),
        ('shoe', 'Shoe Size'),
    ], string='Size Type', required=True)
    
    available_sizes = fields.Many2many('uniform.size', string='Available Sizes')
    
    # Stock and procurement information
    qty_available = fields.Integer('Quantity Available', default=0)
    min_qty = fields.Integer('Minimum Quantity', default=5)
    
    # Replacement policy
    replacement_period = fields.Integer('Replacement Period (months)', default=12,
                                       help="Number of months after which the item is eligible for replacement")
    
    # Tracking issued uniforms
    assignment_ids = fields.One2many('uniform.assignment', 'item_id', string='Assignments')
    assignment_count = fields.Integer(compute='_compute_assignment_count', string='Assignment Count')
    
    @api.depends('assignment_ids')
    def _compute_assignment_count(self):
        for item in self:
            item.assignment_count = len(item.assignment_ids)
    
    # For tracking purposes, return count
    return_count = fields.Integer(compute='_compute_return_count', string='Return Count')
    
    @api.depends('assignment_ids.return_ids')
    def _compute_return_count(self):
        for item in self:
            return_count = 0
            for assignment in item.assignment_ids:
                return_count += len(assignment.return_ids)
            item.return_count = return_count
