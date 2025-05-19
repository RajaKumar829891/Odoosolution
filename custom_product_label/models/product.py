from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    default_location_id = fields.Many2one(
        'stock.location', 
        string='Default Location',
        help="Default location where this product is stored"
    )
    
    def action_print_custom_label(self):
        """ Print the custom 50*25mm label directly """
        self.ensure_one()
        products = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
        return self.env.ref('custom_product_label.action_report_custom_product_label').report_action(products)


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    def action_print_custom_label(self):
        """ Print the custom 50*25mm label directly """
        return self.env.ref('custom_product_label.action_report_custom_product_label').report_action(self)
