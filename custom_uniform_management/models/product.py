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
    
    # We remove the available_sizes One2many field as we'll use product attributes instead
    
    @api.onchange('is_uniform')
    def _onchange_is_uniform(self):
        if self.is_uniform:
            if not self.uniform_type:
                self.uniform_type = 'other'
            # Set the product type to storable product
            self.detailed_type = 'product'
            # Ensure product uses variants
            self.has_dynamic_attributes = True
            
            # Create 'Size' attribute if it doesn't exist and link to this product
            self._ensure_size_attribute()
        else:
            self.uniform_type = False
    
    def _ensure_size_attribute(self):
        """Create or find the Size attribute and associate it with this product"""
        AttributeModel = self.env['product.attribute']
        size_attribute = AttributeModel.search([('name', '=', 'Size')], limit=1)
        
        if not size_attribute:
            size_attribute = AttributeModel.create({
                'name': 'Size',
                'create_variant': 'always',
                'display_type': 'select',
            })
            
        # Check if this product already has the size attribute
        has_size = False
        for attr_line in self.attribute_line_ids:
            if attr_line.attribute_id.id == size_attribute.id:
                has_size = True
                break
        
        # If product doesn't have size attribute yet, add it
        if not has_size:
            self.attribute_line_ids = [(0, 0, {
                'attribute_id': size_attribute.id,
                'value_ids': []
            })]
    
    def action_add_common_sizes(self):
        """Add common sizes based on uniform type"""
        self.ensure_one()
        if not self.is_uniform:
            return
            
        size_attribute = self.env['product.attribute'].search([('name', '=', 'Size')], limit=1)
        if not size_attribute:
            return
            
        # Find the attribute line for size
        size_line = False
        for line in self.attribute_line_ids:
            if line.attribute_id.id == size_attribute.id:
                size_line = line
                break
                
        if not size_line:
            return
            
        # Define common sizes based on uniform type
        common_sizes = []
        if self.uniform_type in ['shirt', 'jacket']:
            common_sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        elif self.uniform_type == 'pants':
            common_sizes = ['28', '30', '32', '34', '36', '38', '40', '42']
        elif self.uniform_type == 'shoes':
            common_sizes = ['38', '39', '40', '41', '42', '43', '44', '45']
        elif self.uniform_type == 'helmet':
            common_sizes = ['S', 'M', 'L', 'XL']
        elif self.uniform_type == 'gloves':
            common_sizes = ['S', 'M', 'L', 'XL']
        else:
            common_sizes = ['S', 'M', 'L']
            
        # Create missing size values
        values_to_add = []
        existing_values = size_line.value_ids.mapped('name')
        
        for size in common_sizes:
            if size not in existing_values:
                value = self.env['product.attribute.value'].search([
                    ('attribute_id', '=', size_attribute.id),
                    ('name', '=', size)
                ], limit=1)
                
                if not value:
                    value = self.env['product.attribute.value'].create({
                        'attribute_id': size_attribute.id,
                        'name': size
                    })
                    
                values_to_add.append(value.id)
                
        if values_to_add:
            size_line.value_ids = [(4, value_id) for value_id in values_to_add]
