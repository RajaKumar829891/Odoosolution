from odoo import models, fields

class UniformSize(models.Model):
    _name = 'uniform.size'
    _description = 'Uniform Size'
    _order = 'sequence, name'

    name = fields.Char('Size Name', required=True)
    sequence = fields.Integer('Sequence', default=10)
    size_type = fields.Selection([
        ('numeric', 'Numeric (e.g., 40, 42)'),
        ('letter', 'Letter (e.g., S, M, L)'),
        ('shoe', 'Shoe Size'),
    ], string='Size Type', required=True)
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)
    
    # Measurement standards
    chest_measurement = fields.Float('Chest (cm)', digits=(5, 1))
    waist_measurement = fields.Float('Waist (cm)', digits=(5, 1))
    hip_measurement = fields.Float('Hip (cm)', digits=(5, 1))
    length_measurement = fields.Float('Length (cm)', digits=(5, 1))
    foot_length = fields.Float('Foot Length (cm)', digits=(5, 1))
    
    # For converting between different size systems
    equivalent_international = fields.Char('International Equivalent')
    equivalent_us = fields.Char('US Equivalent')
    equivalent_eu = fields.Char('EU Equivalent')
    equivalent_uk = fields.Char('UK Equivalent')
    
    # Related items that have this size
    item_ids = fields.Many2many('uniform.item', string='Uniform Items')
