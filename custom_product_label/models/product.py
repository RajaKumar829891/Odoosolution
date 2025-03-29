from odoo import api, fields, models

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    # This field already exists in stock module, but we're ensuring it's available
    property_stock_inventory = fields.Many2one(
        'stock.location', 
        string="Inventory Location",
        company_dependent=True,
        domain="[('usage', '=', 'inventory')]",
        help="This location will be used as the destination location for inventory loss.")


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    def action_print_custom_label(self):
        """Print custom label for this product"""
        self.ensure_one()
        return self.env.ref('custom_product_label.action_report_custom_product_label').report_action(self.product_variant_ids)
