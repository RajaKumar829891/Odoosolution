from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    google_maps_api_key = fields.Char(
        string='Google Maps API Key',
        config_parameter='fleet_booking.google_maps_api_key',
        default_model='res.config.settings'  # Added this
    )
    
    auto_calculate_route_details = fields.Boolean(
        string='Auto Calculate Route Details',
        config_parameter='fleet_booking.auto_calculate_route_details',
        default=True,
        default_model='res.config.settings'  # Added this
    )
    
    default_distance_uom = fields.Selection(
        [('km', 'Kilometer'), ('mile', 'Mile')],
        string='Default Distance UOM',
        default_model='res.config.settings',  # You already have this
        config_parameter='fleet_booking.default_distance_uom',
        default='km'
        # Removed the domain since it doesn't make sense for Selection fields
    )
    
    auto_calculate_price = fields.Boolean(
        string='Auto Calculate Price',
        config_parameter='fleet_booking.auto_calculate_price',
        default=True,
        default_model='res.config.settings'  # Added this
    )
    
    default_vat_percentage = fields.Float(
        string='Default VAT Percentage',
        config_parameter='fleet_booking.default_vat_percentage',
        default=18.0,
        default_model='res.config.settings'  # Added this
    )
    
    # Removed distance_uom as it's a duplicate of default_distance_uom
    # If you need it separately, it would look like this:
    # distance_uom = fields.Selection(
    #     [('km', 'Kilometer'), ('mile', 'Mile')],
    #     string='Distance Unit',
    #     config_parameter='fleet_booking.distance_uom',  # Use different parameter name
    #     default='km',
    #     default_model='res.config.settings'
    # )