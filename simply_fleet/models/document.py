from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

def post_init_hook(cr, registry):
   cr.execute("""
       INSERT INTO simply_fleet_document_name (name, active, create_uid, create_date, write_uid, write_date)
       SELECT DISTINCT d.name, true, 1, NOW(), 1, NOW()
       FROM simply_fleet_document d
       WHERE d.name NOT IN (SELECT name FROM simply_fleet_document_name)
       AND d.name IS NOT NULL
       ON CONFLICT ON CONSTRAINT simply_fleet_document_name_unique_document_name DO NOTHING;
   """)
   
   cr.execute("""
       INSERT INTO simply_fleet_issuing_authority (name, active, create_uid, create_date, write_uid, write_date)
       SELECT DISTINCT d.issuing_authority, true, 1, NOW(), 1, NOW()
       FROM simply_fleet_document d
       WHERE d.issuing_authority NOT IN (SELECT name FROM simply_fleet_issuing_authority)
       AND d.issuing_authority IS NOT NULL
       ON CONFLICT ON CONSTRAINT simply_fleet_issuing_authority_unique_authority_name DO NOTHING;
   """)

class DocumentName(models.Model):
   _name = 'simply.fleet.document.name'
   _description = 'Document Names'
   _rec_name = 'name'

   name = fields.Char(string='Name', required=True)
   description = fields.Text(string='Description')
   active = fields.Boolean(default=True)

   _sql_constraints = [
       ('unique_document_name', 'UNIQUE(name)', 'Document name must be unique!')
   ]

class IssuingAuthority(models.Model):
   _name = 'simply.fleet.issuing.authority'
   _description = 'Issuing Authorities'
   _rec_name = 'name'

   name = fields.Char(string='Name', required=True)
   description = fields.Text(string='Description')
   active = fields.Boolean(default=True)

   _sql_constraints = [
       ('unique_authority_name', 'UNIQUE(name)', 'Authority name must be unique!')
   ]

class DocumentReminder(models.Model):
   _name = 'simply.fleet.document.reminder'
   _description = 'Document Reminders'
   _order = 'days_before'

   document_id = fields.Many2one('simply.fleet.document', string='Document')
   days_before = fields.Integer(string='Days Before Expiry', required=True)
   reminder_type = fields.Selection([
       ('email', 'Email'),
       ('notification', 'System Notification'),
       ('both', 'Both')
   ], string='Reminder Type', required=True, default='both')
   is_active = fields.Boolean(string='Active', default=True)
   
   _sql_constraints = [
       ('unique_reminder_days', 
        'UNIQUE(document_id, days_before)',
        'You cannot set multiple reminders for the same number of days!')
   ]

class Document(models.Model):
   _name = 'simply.fleet.document'
   _description = 'Vehicle Documents'
   _inherit = ['mail.thread', 'mail.activity.mixin']
   _order = 'expiry_date'

   name = fields.Char(string='Document Name', required=True, tracking=True)
   vehicle_id = fields.Many2one('simply.fleet.vehicle', string='Vehicle', required=True, tracking=True)
   document_number = fields.Char(string='Document Number', tracking=True)
   issue_date = fields.Date(string='Issue Date', required=True, tracking=True)
   expiry_date = fields.Date(string='Expiry Date', required=True, tracking=True)
   document_file = fields.Binary(string='Document File', required=True, attachment=True)
   file_name = fields.Char(string='File Name')
   notes = fields.Text(string='Notes')
   issuing_authority = fields.Char(string='Issuing Authority', tracking=True)
   renewal_cost = fields.Float(string='Renewal Cost', tracking=True)
   reminder_ids = fields.One2many('simply.fleet.document.reminder', 'document_id', string='Reminders')
   last_renewal_date = fields.Date(string='Last Renewal Date', tracking=True)
   next_renewal_date = fields.Date(string='Next Renewal Date', compute='_compute_next_renewal_date', store=True)
   state = fields.Selection([
       ('valid', 'Valid'),
       ('expired', 'Expired'),
       ('expiring_soon', 'Expiring Soon')
   ], string='Status', compute='_compute_document_status', store=True, tracking=True)
   days_to_expire = fields.Integer(string='Days to Expire', compute='_compute_days_to_expire', store=True)
   active = fields.Boolean(default=True)

   @api.model
   def _update_document_expiry_status(self):
       today = fields.Date.today()
       documents = self.search([('expiry_date', '!=', False)])
       for doc in documents:
           delta = doc.expiry_date - today
           doc.days_to_expire = max(delta.days, 0)
           doc._compute_document_status()

   @api.depends('expiry_date')
   def _compute_days_to_expire(self):
       today = fields.Date.today()
       for record in self:
           if record.expiry_date:
               delta = record.expiry_date - today
               record.days_to_expire = max(delta.days, 0)
           else:
               record.days_to_expire = 0

   @api.depends('expiry_date', 'reminder_ids.days_before')
   def _compute_document_status(self):
       today = fields.Date.today()
       for record in self:
           if not record.expiry_date:
               record.state = 'valid'
           elif record.expiry_date < today:
               record.state = 'expired'
           elif (record.expiry_date - today).days <= 30:
               record.state = 'expiring_soon'
           else:
               record.state = 'valid'

   @api.depends('expiry_date')
   def _compute_next_renewal_date(self):
       for record in self:
           if record.expiry_date:
               record.next_renewal_date = record.expiry_date
           else:
               record.next_renewal_date = False

   @api.constrains('issue_date', 'expiry_date')
   def _check_dates(self):
       for record in self:
           if record.issue_date and record.expiry_date:
               if record.issue_date > record.expiry_date:
                   raise ValidationError('Issue Date cannot be later than Expiry Date')

   def _generate_document_reminder_notifications(self):
       today = fields.Date.today()
       expiring_documents = self.search([
           ('state', '=', 'expiring_soon'),
           ('active', '=', True)
       ])
       
       for doc in expiring_documents:
           if doc.reminder_ids:
               for reminder in doc.reminder_ids:
                   if reminder.is_active:
                       if reminder.reminder_type in ['email', 'both']:
                           pass
                       if reminder.reminder_type in ['notification', 'both']:
                           pass
