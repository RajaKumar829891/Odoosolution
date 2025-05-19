from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime

class FleetPaymentRegisterWizard(models.TransientModel):
    _name = 'fleet.payment.register.wizard'
    _description = 'Register Payment for Booking'
    
    booking_id = fields.Many2one('fleet.booking', string='Booking', 
                                required=True, ondelete='cascade')
    amount = fields.Monetary(string='Amount', required=True)
    currency_id = fields.Many2one(related='booking_id.currency_id', string='Currency')
    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('other', 'Other'),
    ], string='Payment Method', required=True, default='bank_transfer')
    payment_date = fields.Datetime(string='Payment Date', required=True, 
                                  default=lambda self: fields.Datetime.now())
    notes = fields.Text(string='Notes')
    
    @api.onchange('booking_id')
    def _onchange_booking_id(self):
        if self.booking_id:
            self.amount = self.booking_id.balance_amount
    
    def action_register_payment(self):
        self.ensure_one()
        
        if self.amount <= 0:
            raise ValidationError(_("Payment amount must be greater than zero."))
        
        if self.amount > self.booking_id.balance_amount:
            raise ValidationError(_("Payment amount cannot exceed the balance amount."))
        
        # Update booking payment information
        new_amount_paid = self.booking_id.amount_paid + self.amount
        
        # Determine the new payment status
        if new_amount_paid >= self.booking_id.total_price:
            payment_status = 'paid'
        elif new_amount_paid > 0:
            payment_status = 'partially_paid'
        else:
            payment_status = self.booking_id.payment_status
        
        # Update the booking
        self.booking_id.write({
            'amount_paid': new_amount_paid,
            'payment_method': self.payment_method,
            'payment_date': self.payment_date,
            'payment_status': payment_status,
        })
        
        # Add a note in the chatter
        message = _("Payment of %s %s registered on %s via %s") % (
            self.amount, 
            self.currency_id.name, 
            self.payment_date, 
            dict(self._fields['payment_method'].selection).get(self.payment_method),
        )
        
        if self.notes:
            message += _(": %s") % self.notes
        
        self.booking_id.message_post(body=message)
        
        return {'type': 'ir.actions.act_window_close'}