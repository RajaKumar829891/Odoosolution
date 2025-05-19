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
    
    @api.onchange('is_uniform')
    def _onchange_is_uniform(self):
        if self.is_uniform:
            if not self.uniform_type:
                self.uniform_type = 'other'
            # Set the product type to storable product
            self.detailed_type = 'product'  
        else:
            self.uniform_type = False
            
    def get_available_variants_quantity(self):
        """Return a dictionary of variant_id: available_quantity"""
        self.ensure_one()
        result = {}
        for variant in self.product_variant_ids:
            # Get the available quantity from stock quants
            available_qty = self.env['stock.quant'].search([
                ('product_id', '=', variant.id),
                ('location_id.usage', '=', 'internal')
            ]).mapped('quantity')
            result[variant.id] = sum(available_qty)
        return result