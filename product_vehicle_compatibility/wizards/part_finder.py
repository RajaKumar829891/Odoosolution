from odoo import models, fields, api

class VehiclePartFinderWizard(models.TransientModel):
    _name = 'simply.fleet.part.finder.wizard'
    _description = 'Find Parts Compatible with Vehicle'
    
    # Selection fields
    vehicle_id = fields.Many2one(
        'simply.fleet.vehicle',
        string='Vehicle',
        help='Find parts compatible with this specific vehicle'
    )
    vehicle_type_id = fields.Many2one(
        'simply.fleet.vehicle.type',
        string='Vehicle Type',
        help='Find parts compatible with this vehicle type'
    )
    product_category_id = fields.Many2one(
        'product.category',
        string='Product Category',
        help='Filter compatible parts by category'
    )
    include_vehicle_specific = fields.Boolean(
        string='Include Vehicle-Specific Parts',
        default=True,
        help='Include parts compatible with the specific vehicle'
    )
    include_type_specific = fields.Boolean(
        string='Include Type-Specific Parts',
        default=True,
        help='Include parts compatible with this vehicle type'
    )
    
    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        if self.vehicle_id:
            self.vehicle_type_id = self.vehicle_id.vehicle_type_id
    
    def action_find_parts(self):
        """Find compatible parts based on selection"""
        self.ensure_one()
        domain = []
        
        # Build domain based on selections
        if self.include_vehicle_specific and self.vehicle_id:
            domain.append(('compatible_vehicle_ids', 'in', self.vehicle_id.id))
            
        if self.include_type_specific and self.vehicle_type_id:
            type_condition = ('compatible_vehicle_type_ids', 'in', self.vehicle_type_id.id)
            if domain:
                # Use OR condition between vehicle-specific and type-specific
                domain = ['|'] + domain + [type_condition]
            else:
                domain.append(type_condition)
                
        if self.product_category_id:
            domain.append(('categ_id', 'child_of', self.product_category_id.id))
            
        # If no conditions specified, show an error
        if not domain:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'Please specify at least one search criteria',
                    'type': 'danger',
                }
            }
            
        # Return action to display results
        return {
            'name': 'Compatible Parts',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {
                'search_default_filter_to_purchase': 1,
            },
            'target': 'current',
        }
