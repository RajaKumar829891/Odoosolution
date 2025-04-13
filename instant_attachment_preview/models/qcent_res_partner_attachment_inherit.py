# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments',help="Upload attachments for preview",)
