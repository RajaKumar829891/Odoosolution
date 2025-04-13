# -*- coding: utf-8 -*-
from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order.line'

    attachment_ids = fields.Many2many('ir.attachment',string='Attachments',help="Upload attachments for preview", )
