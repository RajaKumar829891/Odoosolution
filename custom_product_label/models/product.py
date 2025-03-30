from odoo import api, fields, models

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    def action_print_custom_label(self):
        """Print custom label for this product"""
        self.ensure_one()
        return self.env.ref('custom_product_label.action_report_custom_product_label').report_action(self)

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    def action_print_custom_label(self):
        """Print custom label for this product"""
        self.ensure_one()
        return self.env.ref('custom_product_label.action_report_custom_product_label').report_action(self.product_variant_ids)
