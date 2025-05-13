import os
from odoo import models, fields, api
from odoo.tools import config


class GoogleAPIKeyManager(models.Model):
    _name = 'google.api.key.manager'
    _description = 'Manage Google API Key Retrieval'

    google_api_key = fields.Char(string="Google API Key", readonly=True)

    def _get_api_key_from_system_parameters(self):
        """Retrieve API key from system parameters (low security)."""
        return self.env['ir.config_parameter'].sudo().get_param('google_api_key')

    @api.model
    def get_google_api_key(self):
        """Retrieve Google API key from system parameters."""
        return self._get_api_key_from_system_parameters()

    @api.model
    def set_google_api_key(self, api_key):
        """Store Google API key into system parameters."""
        self.env['ir.config_parameter'].sudo().set_param('google_api_key', api_key)