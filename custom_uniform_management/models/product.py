from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    # Instead of adding a new product type, we'll use a boolean field
    is_uniform = fields.Boolean(string='Is Uniform', default=False)
    
    uniform_type = fields.Selection([
        ('shirt', 'Shirt'),
        ('pants', 'Pants'),
        ('shoes', 'Shoes'),
        ('id_card', 'ID Card'),
        ('helmet', 'Helmet'),
        ('gloves', 'Gloves'),
        ('jacket', 'Jacket'),
        ('other', 'Other')
    ], string='Uniform Type')
    
    available_sizes = fields.One2many('uniform.item.size', 'product_id', string='Available Sizes')
    
    @api.onchange('is_uniform')
    def _onchange_is_uniform(self):
        if self.is_uniform:
            if not self.uniform_type:
                self.uniform_type = 'other'
            # Set the product type to storable product
            self.detailed_type = 'product'  
        else:
            self.uniform_type = False


class UniformItemSize(models.Model):
    _name = 'uniform.item.size'
    _description = 'Uniform Item Size'
    
    name = fields.Char(string='Size Name', required=True)
    product_id = fields.Many2one('product.template', string='Uniform Item', required=True, ondelete='cascade')
    uniform_type = fields.Selection(related='product_id.uniform_type', readonly=True)
    quantity = fields.Integer(string='Available Quantity', default=0)
    
    _sql_constraints = [
        ('unique_product_size', 'UNIQUE(product_id, name)', 'This size already exists for this uniform item!')
    ]
