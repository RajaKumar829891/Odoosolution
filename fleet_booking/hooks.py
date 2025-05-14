import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def set_google_maps_api_key(cr, registry):
    """Set Google Maps API key in system parameters if not already set"""
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Check if API key is already set
        api_key = env['ir.config_parameter'].get_param('fleet_booking.google_maps_api_key')
        
        if not api_key:
            # If not set, add a placeholder key (you'll replace this with your actual key)
            env['ir.config_parameter'].set_param(
                'fleet_booking.google_maps_api_key', 
                'AIzaSyB6yP-T09O2hB-cEG8d0-WhPXcSJnDkgro'
            )
            _logger.info("Set placeholder for Google Maps API key. Please update with actual key.")