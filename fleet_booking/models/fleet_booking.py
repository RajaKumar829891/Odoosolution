from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, time



class FleetBooking(models.Model):
    _name = 'fleet.booking'
    _description = 'Fleet Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Order Reference', required=True, copy=False, 
                       readonly=True, default=lambda self: _('New'))
    
    # Basic Info
    customer_id = fields.Many2one('res.partner', string='Customer', 
                                  required=True, tracking=True)
    customer_email = fields.Char(related='customer_id.email', string='Email')
    customer_phone = fields.Char(related='customer_id.phone', string='Phone')
    company_name = fields.Char(string='Company Name')
    route_id = fields.Many2one('fleet.route', string='Route')
    
    # Passenger Info
    passenger_name = fields.Char(string='Passenger Name')
    passenger_position = fields.Char(string='Passenger Position')
    passenger_email = fields.Char(string='Passenger Email')
    passenger_phone = fields.Char(string='Passenger Phone')
    passenger_count = fields.Integer(string='Passenger Count', default=0)
    
    # Status management
    state = fields.Selection([
        ('enquiry', 'Enquiry'),
        ('quotation', 'Quotation'),
        ('followup', 'Follow Up'),
        ('confirmed_pending', 'Confirmed (Lost/Cancelled)'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('feedback', 'Feedback'),
    ], string='Status', default='enquiry', tracking=True)
    
    # Transport Details
    journey_start_location = fields.Char(string='Start Location', tracking=True)
    journey_end_location = fields.Char(string='End Location', tracking=True)
    via_stops = fields.Text(string='Via Stops')
    journey_distance = fields.Float(string='Distance', digits=(16, 2))
    distance_uom = fields.Selection([
        ('km', 'Kilometer'),
        ('mile', 'Mile')
    ], string='Distance UOM', default='km')
    
    journey_duration = fields.Integer(string='Duration (minutes)')
    journey_start_date = fields.Date(string='Travel Date', tracking=True)
    journey_start_time = fields.Selection(
        selection='_get_time_options',
        string='Start Time',
        default='08:00 AM'
    )
    fixed_end_time = fields.Boolean(string='Fixed End Time')
    return_journey_needed = fields.Boolean(string='Return Journey Needed')

    return_journey_date = fields.Date(string='Return Date', tracking=True)
    return_journey_time = fields.Selection(
        selection='_get_time_options',
        string='Return Time',
        default='08:00 AM'
    )
    
    # Vehicle Details
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    vehicle_type = fields.Selection([
        ('17_Seater_Luxury_force_Traveller', '17 Seater Luxury force Traveller'),
        ('26_Seater_Luxury_Force_Traveller', '26 Seater Luxury Force Traveller'),
        ('33_Seater_Super_Luxury_Recliner_AC_Coach', '33 Seater Super Luxury Recliner AC Coach'),
        ('41_Seater_Super_Luxury_Recliner_AC_Coach', '41 Seater Super Luxury Recliner AC Coach'),
        ('48_Seater_Luxury_AC_Coach', '48 Seater Luxury AC Coach'),
        ('49_Seater_Super_Luxury_AC_Coach_2024', '49 Seater Super Luxury AC Coach 2024'),
        ('50_Seater_Super_Luxury_AC_Coach_2025', '50 Seater Super Luxury AC Coach 2025'),
        ('Toyota_Innova', 'Toyota Innova'),
        ('Toyota_Innova_Crysta', 'Toyota Innova Crysta'),
        ('Ertiga', 'Ertiga'),
        ('Honda_Amaze', 'Honda Amaze'),
        ('Hyundai_Aura', 'Hyundai Aura'),
        ('Hyundai_Xcent', 'Hyundai Xcent'),
        ('Tavera', 'Tavera'),
    ], string='Vehicle Type')
    
    # Driver Assignment
    driver_id = fields.Many2one('fleet.driver', string='Assigned Driver')
    
    # Cargo Details
    cargo_type = fields.Selection([
        ('passenger', 'Passenger'),
        ('luggage', 'Luggage'),
        ('freight', 'Freight'),
    ], string='Cargo Type', default='passenger')
    suitcase_count = fields.Integer(string='Suitcase Count', default=0)
    hand_luggage_count = fields.Integer(string='Hand Luggage Count', default=0)
    cargo_manifest_id = fields.Many2one('fleet.cargo.manifest', string='Cargo Manifest')
    
    # Financial Details
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    journey_price = fields.Monetary(string='Journey Price', currency_field='currency_id')
    gst_percentage = fields.Selection([
        ('0', '0%'),
        ('5', '5%'),
        ('12', '12%'),
    ], string='GST %', default='5', tracking=True)

    vat_amount = fields.Monetary(string='GST', currency_field='currency_id', 
                                compute='_compute_gst_amount', store=True, readonly=True)
    total_price = fields.Monetary(string='Total', compute='_compute_total_price', 
                                    store=True, currency_field='currency_id')
    
    # Payment Tracking
    payment_status = fields.Selection([
        ('not_invoiced', 'Not Invoiced'),
        ('invoiced', 'Invoiced'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
    ], string='Payment Status', default='not_invoiced', tracking=True)
    payment_date = fields.Datetime(string='Payment Date')
    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('other', 'Other'),
    ], string='Payment Method')
    amount_paid = fields.Monetary(string='Amount Paid', currency_field='currency_id')
    balance_amount = fields.Monetary(string='Balance', compute='_compute_balance', 
                                     store=True, currency_field='currency_id')
    
    # Notes
    notes = fields.Text(string='Order Notes')
    transport_notes = fields.Text(string='Transport Notes')
    
    # Activity tracking
    create_date = fields.Datetime(string='Created On', readonly=True)
    user_id = fields.Many2one('res.users', string='Assigned To', 
                              default=lambda self: self.env.user)
    
    # Feedback
    feedback = fields.Text(string='Customer Feedback')
    feedback_rating = fields.Selection([
        ('1', '1 Star'),
        ('2', '2 Stars'),
        ('3', '3 Stars'),
        ('4', '4 Stars'),
        ('5', '5 Stars'),
    ], string='Rating')

    # Add this field if not already present
    company_id = fields.Many2one('res.company', string='Company', 
                               default=lambda self: self.env.company)
    
    # Add these new fields
    route_map_url = fields.Char(string='Route Map URL')
    journey_duration_formatted = fields.Char(
        string='Duration (Formatted)', 
        compute='_compute_duration_formatted'
    )
    
    # NEW FIELDS FOR DYNAMIC TERMS AND CONDITIONS
    terms_template_id = fields.Many2one('fleet.booking.terms.template', string='Terms Template')
    terms_conditions = fields.Html(string='Terms & Conditions', help='Custom terms and conditions for this booking')
    
    @api.onchange('terms_template_id')
    def _onchange_terms_template(self):
        """Apply the selected template to terms_conditions"""
        if self.terms_template_id:
            self.terms_conditions = self.terms_template_id.template_content
    
    def action_generate_invoice(self):
        """Generate and show invoice"""
        self.ensure_one()
        # Update status
        self.write({'payment_status': 'invoiced'})
        
        # Return the invoice report action
        return self.env.ref('fleet_booking.action_report_fleet_booking_invoice').report_action(self)
    
    def action_view_invoice(self):
        """View the invoice"""
        self.ensure_one()
        return self.env.ref('fleet_booking.action_report_fleet_booking_invoice').report_action(self)
    
    def action_download_invoice(self):
        """Download the invoice as PDF"""
        self.ensure_one()
        return self.env.ref('fleet_booking.action_report_fleet_booking_invoice').report_action(self)

    @api.depends('journey_price', 'vat_amount')
    def _compute_total_price(self):
        for record in self:
            record.total_price = record.journey_price + record.vat_amount
    
    @api.depends('journey_price', 'gst_percentage')
    def _compute_gst_amount(self):
        for record in self:
            if record.journey_price and record.gst_percentage:
                gst_rate = float(record.gst_percentage) / 100.0
                record.vat_amount = record.journey_price * gst_rate
            else:
                record.vat_amount = 0.0

    @api.depends('total_price', 'amount_paid')
    def _compute_balance(self):
        for record in self:
            record.balance_amount = record.total_price - record.amount_paid

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('fleet.booking') or _('New')
        return super(FleetBooking, self).create(vals_list)

    def action_quotation(self):
        self.write({'state': 'quotation'})

    def action_followup(self):
        self.write({'state': 'followup'})

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_lost_cancelled(self):
        self.write({'state': 'confirmed_pending'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_feedback(self):
        self.write({'state': 'feedback'})

    def action_reset_to_enquiry(self):
        self.write({'state': 'enquiry'})

    def action_assign_driver(self):
        return {
            'name': _('Assign Driver'),
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.driver.assign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_booking_id': self.id},
        }

    def action_register_payment(self):
        return {
            'name': _('Register Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.payment.register.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_booking_id': self.id, 'default_amount': self.balance_amount},
        }

    def action_view_route(self):
        return {
            'name': _('Journey Route'),
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.route',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_start_location': self.journey_start_location,
                'default_end_location': self.journey_end_location,
                'default_via_stops': self.via_stops,
            },
        }
    
    @api.depends('journey_duration')
    def _compute_duration_formatted(self):
        for record in self:
            if record.journey_duration:
                hours = int(record.journey_duration // 60)
                minutes = int(record.journey_duration % 60)
                record.journey_duration_formatted = f"{hours}h {minutes}m"
            else:
                record.journey_duration_formatted = "0h 0m"

    def action_view_route(self):
        """Open route in Google Maps"""
        self.ensure_one()
        if self.journey_start_location and self.journey_end_location:
            base_url = "https://www.google.com/maps/dir/"
            url = base_url + f"{self.journey_start_location}/{self.journey_end_location}"
            
            if self.via_stops:
                stops = self.via_stops.split('\n')
                for stop in stops:
                    if stop.strip():
                        url += f"/{stop.strip()}"
            
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }
    
    def _convert_time_str_to_float(self, time_str):
        """Convert time string (like '09:30 AM') to float (9.5)"""
        if not time_str:
            return 0.0
        
        try:
            # Parse the time string
            time_obj = datetime.strptime(time_str, '%I:%M %p').time()
            # Convert to float (hours + minutes/60)
            return time_obj.hour + time_obj.minute / 60.0
        except Exception:
            return 0.0

    def _convert_float_to_time_str(self, time_float):
        """Convert float time (like 9.5) to string (like '09:30 AM')"""
        if not time_float:
            return ''
        
        try:
            # Convert float to hours and minutes
            hours = int(time_float)
            minutes = int((time_float - hours) * 60)
            
            # Create time object
            time_obj = time(hour=hours % 12 or 12, minute=minutes)
            
            # Format with AM/PM
            period = 'AM' if hours < 12 else 'PM'
            return time_obj.strftime('%I:%M') + ' ' + period
        except Exception:
            return ''
    
    def _convert_time_str_to_minutes(self, time_str):
        """Convert AM/PM time string to minutes since midnight"""
        if not time_str:
            return 0
        
        try:
            from datetime import datetime
            time_obj = datetime.strptime(time_str, '%I:%M %p')
            return time_obj.hour * 60 + time_obj.minute
        except Exception:
            return 0
    
    @api.model
    def _get_time_options(self):
        """Generate time options in 30-minute intervals with AM/PM format"""
        options = []
        
        # Add options for AM period (midnight to noon)
        options.append(('12:00 AM', '12:00 AM'))
        options.append(('12:30 AM', '12:30 AM'))
        
        for hour in range(1, 12):
            options.append((f'{hour:02d}:00 AM', f'{hour:02d}:00 AM'))
            options.append((f'{hour:02d}:30 AM', f'{hour:02d}:30 AM'))
        
        # Add options for PM period (noon to midnight)
        options.append(('12:00 PM', '12:00 PM'))
        options.append(('12:30 PM', '12:30 PM'))
        
        for hour in range(1, 12):
            options.append((f'{hour:02d}:00 PM', f'{hour:02d}:00 PM'))
            options.append((f'{hour:02d}:30 PM', f'{hour:02d}:30 PM'))
        
        return options
    
    @api.onchange('return_journey_needed')
    def _onchange_return_journey(self):
        """Clear return journey fields when return journey is not needed"""
        if not self.return_journey_needed:
            self.return_journey_date = False
            self.return_journey_time = False
    
    @api.onchange('return_journey_needed', 'journey_start_date', 'return_journey_date')
    def _onchange_return_journey_date(self):
        if self.return_journey_needed and self.journey_start_date and self.return_journey_date:
            if self.return_journey_date < self.journey_start_date:
                return {'warning': {
                    'title': _("Invalid Return Date"),
                    'message': _("Return journey date cannot be earlier than outbound journey date.")
                }}


# NEW MODEL FOR TERMS AND CONDITIONS TEMPLATES
class FleetBookingTermsTemplate(models.Model):
    _name = 'fleet.booking.terms.template'
    _description = 'Fleet Booking Terms and Conditions Templates'
    _order = 'sequence, name'
    
    name = fields.Char(string='Template Name', required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    template_content = fields.Html(string='Template Content', required=True)
    
    @api.model
    def create_default_templates(self):
        """Create default terms and conditions templates"""
        default_templates = [
            {
                'name': 'Standard Terms',
                'sequence': 1,
                'template_content': '''
                <h5>Standard Terms and Conditions</h5>
                <ol>
                    <li><strong>Booking Confirmation:</strong> Your booking is confirmed upon receipt of payment.</li>
                    <li><strong>Cancellation Policy:</strong> 24 hours notice required for cancellations.</li>
                    <li><strong>Payment Terms:</strong> Full payment required before service.</li>
                    <li><strong>Vehicle Maintenance:</strong> All vehicles are regularly serviced and maintained.</li>
                    <li><strong>Driver Responsibility:</strong> All our drivers are licensed and insured.</li>
                </ol>
                '''
            },
            {
                'name': 'Basic Terms',
                'sequence': 2,
                'template_content': '''
                <h5>Basic Terms and Conditions</h5>
                <ul>
                    <li>Payment due upon completion of service</li>
                    <li>Cancellation fees may apply</li>
                    <li>All vehicles are insured and maintained</li>
                    <li>Professional drivers provided</li>
                </ul>
                '''
            },
            {
                'name': 'Corporate Terms',
                'sequence': 3,
                'template_content': '''
                <h5>Corporate Client Terms and Conditions</h5>
                <ol>
                    <li><strong>Monthly Billing:</strong> Corporate accounts will be billed monthly.</li>
                    <li><strong>Credit Terms:</strong> Net 30 days from invoice date.</li>
                    <li><strong>Volume Discounts:</strong> Applicable as per corporate agreement.</li>
                    <li><strong>Service Standards:</strong> All services provided as per SLA.</li>
                    <li><strong>Dedicated Support:</strong> Priority customer service for corporate clients.</li>
                </ol>
                '''
            },
            {
                'name': 'Event Transport Terms',
                'sequence': 4,
                'template_content': '''
                <h5>Event Transportation Terms</h5>
                <p>Special terms for event and group transportation:</p>
                <ul>
                    <li>Group bookings require 50% advance payment</li>
                    <li>Final passenger count must be confirmed 48 hours prior</li>
                    <li>Additional charges apply for extra stops</li>
                    <li>Vehicles will be decorated as per requirements</li>
                    <li>Backup vehicle on standby for large groups</li>
                </ul>
                '''
            },
            {
                'name': 'Budget-Friendly Terms',
                'sequence': 5,
                'template_content': '''
                <h5>Budget-Friendly Service Terms</h5>
                <p>Simplified terms for economical services:</p>
                <ol>
                    <li>Cash payment preferred</li>
                    <li>Basic vehicle amenities included</li>
                    <li>Fixed route - no additional stops</li>
                    <li>No cancellation after booking</li>
                    <li>Economy vehicles only</li>
                </ol>
                '''
            }
        ]
        
        for template_data in default_templates:
            existing = self.search([('name', '=', template_data['name'])], limit=1)
            if not existing:
                self.create(template_data)