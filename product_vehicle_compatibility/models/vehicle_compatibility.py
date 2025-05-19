from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    compatible_vehicle_ids = fields.Many2many(
        'simply.fleet.vehicle',
        'product_vehicle_compatibility_rel',
        'product_id',
        'vehicle_id',
        string='Compatible Vehicles',
        help='Select the vehicles this part is compatible with'
    )
    
    compatible_vehicle_count = fields.Integer(
        string='Compatible Vehicle Count',
        compute='_compute_compatible_vehicle_count'
    )
    
    @api.depends('compatible_vehicle_ids')
    def _compute_compatible_vehicle_count(self):
        for product in self:
            product.compatible_vehicle_count = len(product.compatible_vehicle_ids)
    
    def action_open_vehicle_selector(self):
        """Action to open vehicle selector from anywhere in the workflow"""
        self.ensure_one()
        return {
            'name': 'Select Compatible Vehicles',
            'type': 'ir.actions.act_window',
            'res_model': 'simply.fleet.vehicle',
            'view_mode': 'tree,form',
            'target': 'new',
            'domain': [('active', '=', True)],
            'context': {
                'default_compatible_vehicle_ids': self.compatible_vehicle_ids.ids,
                'search_default_active': 1,
                'product_id': self.id,
                'multi_select': True
            }
        }


class Vehicle(models.Model):
    _inherit = 'simply.fleet.vehicle'
    
    compatible_product_ids = fields.Many2many(
        'product.template',
        'product_vehicle_compatibility_rel',
        'vehicle_id',
        'product_id',
        string='Compatible Parts',
        help='Parts compatible with this vehicle'
    )
    
    compatible_product_count = fields.Integer(
        string='Compatible Parts Count',
        compute='_compute_compatible_product_count'
    )
    
    @api.depends('compatible_product_ids')
    def _compute_compatible_product_count(self):
        for vehicle in self:
            vehicle.compatible_product_count = len(vehicle.compatible_product_ids)
    
    def action_view_compatible_parts(self):
        """Action to view all parts compatible with this vehicle"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Compatible Parts',
            'res_model': 'product.template',
            'view_mode': 'tree,form',
            'domain': [('compatible_vehicle_ids', 'in', self.id)],
            'context': {
                'search_default_filter_to_purchase': 1,
            }
        }


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    def action_select_compatible_vehicles(self):
        """Open vehicle selector from inventory operations"""
        self.ensure_one()
        return self.product_id.product_tmpl_id.action_open_vehicle_selector()
