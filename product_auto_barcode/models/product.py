from odoo import models, api, _
from odoo.exceptions import UserError
import random

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        if not vals.get('barcode'):
            vals['barcode'] = self._generate_unique_barcode()
        return super(ProductTemplate, self).create(vals)

    def _generate_unique_barcode(self):
        for _ in range(100):
            # Generate a random 12-digit number
            number = ''.join([str(random.randint(0, 9)) for _ in range(12)])
            
            # Calculate check digit
            total = 0
            for i in range(12):
                digit = int(number[i])
                if i % 2 == 0:
                    total += digit
                else:
                    total += digit * 3
            
            check_digit = (10 - (total % 10)) % 10
            barcode = number + str(check_digit)
            
            # Check uniqueness
            if not self.search_count([('barcode', '=', barcode)]):
                return barcode
                
        raise UserError(_("Unable to generate unique barcode. Please try again."))

    def generate_missing_barcodes(self):
        for product in self:
            if not product.barcode:
                product.barcode = self._generate_unique_barcode()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Barcodes generated successfully'),
                'type': 'success',
                'sticky': False,
            }
        }
