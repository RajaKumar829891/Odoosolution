from odoo import models, fields

class SimplyFleetTransactionType(models.Model):
    _name = 'simply.fleet.transaction.type'
    _description = 'Fleet Transaction Type'
    _order = 'name'

    name = fields.Char(string='Transaction Type', required=True)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
