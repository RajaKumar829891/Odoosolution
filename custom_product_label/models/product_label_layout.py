from odoo import models, fields, api

class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    # Add the custom format to the selection field
    print_format = fields.Selection(selection_add=[
        ('50_25', '50*25mm'),
    ], ondelete={'50_25': 'set default'})

    def process(self):
        if self.print_format == '50_25':
            # Get products either directly or from templates
            products = self.product_ids
            if not products and self.product_tmpl_ids:
                products = self.env['product.product'].search([
                    ('product_tmpl_id', 'in', self.product_tmpl_ids.ids)
                ])
            
            # Return the report action directly
            return self.env.ref('custom_product_label.action_report_custom_product_label').report_action(products)
        
        # For other formats, use the standard behavior
        return super(ProductLabelLayout, self).process()
