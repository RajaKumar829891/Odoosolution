from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    default_location_id = fields.Many2one(
        'stock.location',
        string='Default Location',
        domain="[('usage', '=', 'internal')]",
        help="This is the default location where the product will be stored."
    )
