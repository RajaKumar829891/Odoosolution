from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import pytz
import logging

_logger = logging.getLogger(__name__)

class SimplyFleetFuelLog(models.Model):
    _name = 'simply.fleet.fuel.log'
    _description = 'Fuel Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'datetime desc, id desc'  # Changed from 'date desc' to 'datetime desc'

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Fuel log reference must be unique!')
    ]

    name = fields.Char(string='Reference', readonly=True, copy=False)
    vehicle_id = fields.Many2one(
        'simply.fleet.vehicle', 
        string='Vehicle', 
        required=True, 
        tracking=True,
        ondelete='restrict',
        index=True
    )
    
    
    # Add attachment field for custom chatter functionality
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'simply_fleet_fuel_log_attachment_rel',
        'fuel_log_id',
        'attachment_id',
        string='Add image',
        domain=[('mimetype', 'ilike', 'image/')],
    )
    
    # Add new field to get vehicle type code
    vehicle_type_code = fields.Char(
        string='Vehicle Type Code',
        compute='_compute_vehicle_type_code',
        store=True,
        help='Code of the vehicle type (bus, car, etc.) for icon display'
    )
    
    # Add related fields for vehicle min and max mileage
    vehicle_min_mileage = fields.Float(
        string='Min Mileage',
        related='vehicle_id.min_mileage',
        store=True
    )
    
    vehicle_max_mileage = fields.Float(
        string='Max Mileage',
        related='vehicle_id.max_mileage',
        store=True
    )
    
    # Add Currency Field
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id.id,
        required=True
    )
    
    # Add DateTime field for date and time
    datetime = fields.Datetime(
        string='Date & Time',
        required=True,
        default=fields.Datetime.now,  # Auto-selects current date and time
        tracking=True
    )
    
    # Keep date field as computed for compatibility
    date = fields.Date(
        string='Date',
        compute='_compute_date',
        store=True,
        tracking=True
    )
    # Add datetime_display field
    datetime_display = fields.Char(
        string='Formatted Date & Time',
        compute='_compute_display_date',
        store=True,
        help='Formatted datetime for display purposes'
    )

    # Add display date computed field
    display_date = fields.Date(
        string='Display Date',
        compute='_compute_display_date',
        store=True
    )
    time_display = fields.Char(
        string='Time',
        compute='_compute_time_display',
        store=True,
        help='Time portion of the datetime field'
    )
    
    show_transaction_type = fields.Boolean(
        compute='_compute_show_transaction_type',
        store=True
    )
    
    transaction_type_id = fields.Many2one(
        'simply.fleet.transaction.type',
        string='Transaction Type',
        ondelete='restrict',
        tracking=True
    )
    
    created_by = fields.Many2one(
        'res.users', 
        string='Created By',
        readonly=True,
        default=lambda self: self.env.user.id,
        ondelete='restrict',
        tracking=True
    )
    
    previous_odometer = fields.Float(
        string='Previous Odometer',
        compute='_compute_previous_odometer',
        store=True,
        tracking=True
    )
    
    distance_travelled = fields.Float(
        string='Distance Travelled (km)',
        compute='_compute_distance_travelled',
        store=True,
        tracking=True
    )

    show_mileage = fields.Boolean(
        compute='_compute_show_mileage',
        store=True
    )

    mileage = fields.Float(
        string='Mileage (km/l)',
        compute='_compute_mileage',
        store=True,
        tracking=True,
        help='Vehicle mileage in kilometers per liter'
    )

    fill_type = fields.Selection([
        ('full', 'Full Tank'),
        ('partial', 'Partial Fill')
    ], string='Fill Type', required=True, default='full', tracking=True)
    
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('cng', 'CNG'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid')
    ], string='Fuel Type', required=True, tracking=True)

    station_type = fields.Selection([
        ('diesel_tanker', 'Diesel Tanker'),
        ('petrol_pump', 'Petrol Pump')
    ], string='Station Type', required=True, tracking=True)
    
    liters = fields.Float(
        string='Quantity', 
        tracking=True,
        required=True,
        help='Fuel quantity in liters'
    )

    # Update to Monetary field
    price_per_liter = fields.Monetary(
        string='Price per Liter', 
        tracking=True,
        required=True,
        currency_field='currency_id'
    )

    # Update to Monetary field
    total_amount = fields.Monetary(
        string='Total Amount', 
        compute='_compute_total_amount', 
        store=True,
        currency_field='currency_id'
    )

    odometer = fields.Float(
        string='Odometer Reading', 
        tracking=True,
        required=True
    )

    notes = fields.Text(string='Notes')

    # New display fields for showing values with units
    liters_display = fields.Char(
        string='Quantity',
        compute='_compute_display_fields',
        store=True
    )

    odometer_display = fields.Char(
        string='Odometer Reading',
        compute='_compute_display_fields',
        store=True
    )

    previous_odometer_display = fields.Char(
        string='Previous Odometer',
        compute='_compute_display_fields',
        store=True
    )

    distance_travelled_display = fields.Char(
        string='Distance Travelled',
        compute='_compute_display_fields',
        store=True
    )

    mileage_display = fields.Char(
        string='Mileage',
        compute='_compute_display_fields',
        store=True
    )

    driver_id = fields.Many2one(
        'hr.employee',
        string='Driver',
        tracking=True,
        domain=[('job_title', 'ilike', 'driver')],
        help='Assigned driver for this vehicle'
    )
    
    # Method to handle the attachment button click
    def action_open_attachments(self):
        """
        Open file browser when attachment button is clicked
        This is used for the custom attachment functionality
        """
        # When clicked, it will trigger the file selection dialog
        # We also want to synchronize attachments between this field and the mail attachments
        self._sync_ir_attachments()
        return {
            'type': 'ir.actions.act_window_close'
        }
    def _handle_attachment_sync(self):
        """Handle synchronization between custom attachment field and mail messages"""
        for record in self:
            try:
                # Get all current mail attachments for this record
                mail_attachments = self.env['ir.attachment'].search([
                    ('res_model', '=', self._name),
                    ('res_id', '=', record.id),
                ])
                
                # Get current custom field attachments
                custom_attachments = record.attachment_ids
                
                # Find which attachments to add/remove from mail
                attachments_to_add = custom_attachments - mail_attachments
                attachments_to_remove = mail_attachments - custom_attachments
                
                # Update mail attachments to match custom field
                for attachment in attachments_to_add:
                    attachment.sudo().write({
                        'res_model': self._name,
                        'res_id': record.id,
                    })
                
                for attachment in attachments_to_remove:
                    attachment.sudo().write({
                        'res_model': self._name,
                        'res_id': record.id,
                    })
                    
                # Trigger mail message refresh
                record._notify_record_by_email({}, {}, force_send=False)
                
            except Exception as e:
                _logger.exception('Error in attachment sync: %s', e)
        
    def _sync_ir_attachments(self):
        """Sync attachments from mail to custom field (one-way sync)"""
        for record in self:
            try:
                # Find the related attachments
                mail_attachments = self.env['ir.attachment'].search([
                    ('res_model', '=', self._name),
                    ('res_id', '=', record.id),
                    ('mimetype', 'ilike', 'image/'),  # Only image files
                ])
                
                # Update custom field if different
                if set(record.attachment_ids.ids) != set(mail_attachments.ids):
                    record.sudo().with_context(skip_attachment_sync=True).write({
                        'attachment_ids': [(6, 0, mail_attachments.ids)]
                    })
                    
            except Exception as e:
                _logger.exception('Error syncing attachments: %s', e)
                
    def unlink(self):
        """Clean up attachments when record is deleted"""
        for record in self:
            # Delete associated attachments
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id),
            ])
            attachments.unlink()
            
        return super().unlink()
    
    def write(self, vals):
        # Track attachment changes before writing
        attachment_changes = {}
        if 'attachment_ids' in vals:
            for record in self:
                attachment_changes[record.id] = {
                    'old': set(record.attachment_ids.ids),
                    'new': set()
                }
                
                # Parse the new attachment IDs from vals
                if vals['attachment_ids']:
                    for command in vals['attachment_ids']:
                        if isinstance(command, (list, tuple)):
                            if command[0] == 6:  # Replace all
                                attachment_changes[record.id]['new'].update(command[2])
                            elif command[0] == 4:  # Add
                                attachment_changes[record.id]['new'].add(command[1])
        
        res = super(SimplyFleetFuelLog, self).write(vals)
        
        # Handle attachment sync based on changes
        if 'attachment_ids' in vals:
            for record in self:
                record._handle_attachment_sync()
                
        return res
    
    # Handle data migration during module upgrade
    @api.model
    def _init_column(self, column_name):
        """ Initialize datetime field based on existing date field during installation """
        result = super()._init_column(column_name)
        
        if column_name == 'datetime':
            # Only execute if we're initializing the datetime column
            query = """
                UPDATE simply_fleet_fuel_log 
                SET datetime = date + interval '12 hours'
                WHERE datetime IS NULL AND date IS NOT NULL
            """
            self.env.cr.execute(query)
            
        return result
    
    # Compute date from datetime for compatibility
    @api.depends('datetime')
    def _compute_date(self):
        for record in self:
            if record.datetime:
                record.date = record.datetime.date()
            else:
                record.date = False
                
    @api.depends('datetime')
    def _compute_time_display(self):
        for record in self:
            if record.datetime:
                # Format the time as HH:MM:SS (fixed: removed extra colon)
                record.time_display = record.datetime.strftime('%H:%M:%S')
            else:
                record.time_display = False  # Fixed spelling of False

    # Compute method for display fields with units
    @api.depends('liters', 'odometer', 'previous_odometer', 'distance_travelled', 'mileage')
    def _compute_display_fields(self):
        for record in self:
            # Format with units (handle zero and None values)
            record.liters_display = f"{record.liters} L" if record.liters else "0 L"
            record.odometer_display = f"{int(record.odometer)} km" if record.odometer else "0 km"
            record.previous_odometer_display = f"{int(record.previous_odometer)} km" if record.previous_odometer else "0 km"
            record.distance_travelled_display = f"{int(record.distance_travelled)} km" if record.distance_travelled else "0 km"
            
            # Only show mileage for full tank fills
            if record.fill_type == 'full' and record.mileage:
                record.mileage_display = f"{round(record.mileage, 2)} km/L"
            else:
                record.mileage_display = "0 km/L"

    # New compute method for vehicle type code
    @api.depends('vehicle_id', 'vehicle_id.vehicle_type_id', 'vehicle_id.vehicle_type_id.code')
    def _compute_vehicle_type_code(self):
        for record in self:
            if record.vehicle_id and record.vehicle_id.vehicle_type_id and record.vehicle_id.vehicle_type_id.code:
                record.vehicle_type_code = record.vehicle_id.vehicle_type_id.code
            else:
                record.vehicle_type_code = 'car'  # Default to car if no type code found

    @api.depends('datetime')
    def _compute_display_date(self):
        for record in self:
            if record.datetime:
                # Get the user's timezone
                user_tz = self.env.user.tz or 'UTC'
                try:
                    # Convert to user's timezone for display purposes
                    dt_as_utc = pytz.UTC.localize(record.datetime.replace(tzinfo=None)) if not record.datetime.tzinfo else record.datetime
                    local_dt = dt_as_utc.astimezone(pytz.timezone(user_tz))
                    
                    # Set both date and time using the timezone-converted datetime
                    # This ensures the date is correct in the user's timezone
                    record.display_date = local_dt.date()
                    record.datetime_display = local_dt.strftime('%I:%M %p')
                except Exception as e:
                    _logger.error(f"Timezone conversion error: {e}")
                    # Fallback to UTC if conversion fails
                    record.display_date = record.datetime.date()
                    record.datetime_display = record.datetime.strftime('%I:%M %p')
            else:
                record.display_date = False
                record.datetime_display = False

    @api.depends('fill_type')
    def _compute_show_mileage(self):
        for record in self:
            record.show_mileage = bool(record.fill_type == 'full')

    @api.onchange('fill_type')
    def _onchange_fill_type(self):
        for record in self:
            if record.fill_type == 'partial':
                record.mileage = False

    @api.depends('station_type')
    def _compute_show_transaction_type(self):
        for record in self:
            # Always hide the transaction type field regardless of station type
            record.show_transaction_type = False

    # Removed the onchange_station_type method as it's no longer needed

    @api.depends('distance_travelled', 'liters', 'fill_type')
    def _compute_mileage(self):
        for record in self:
            if record.fill_type == 'full' and record.liters and record.liters > 0 and record.distance_travelled and record.distance_travelled > 0:
                record.mileage = record.distance_travelled / record.liters
            else:
                record.mileage = 0.0

    @api.depends('liters', 'price_per_liter')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = (record.liters or 0.0) * (record.price_per_liter or 0.0)

    @api.depends('vehicle_id', 'datetime')
    def _compute_previous_odometer(self):
        for record in self:
            if not record.vehicle_id or not record.vehicle_id.exists():
                record.previous_odometer = 0.0
                continue
            
            try:
                # Find the most recent fuel log for this vehicle with a valid odometer reading
                previous_log = self.env['simply.fleet.fuel.log'].search([
                    ('vehicle_id', '=', record.vehicle_id.id),
                    ('datetime', '<', record.datetime or fields.Datetime.now()),  # Use datetime instead of date
                    ('id', '!=', record._origin.id or False),
                    ('odometer', '>', 0)  # Only consider logs with positive odometer values
                ], order='datetime desc, id desc', limit=1)
                
                if previous_log and previous_log.exists():
                    record.previous_odometer = previous_log.odometer
                else:
                    # If no previous log exists, use the vehicle's initial odometer or 0
                    record.previous_odometer = record.vehicle_id.initial_odometer if record.vehicle_id.initial_odometer else 0.0
            except Exception as e:
                _logger.error(f"Error computing previous odometer: {e}")
                record.previous_odometer = 0.0

    @api.depends('odometer', 'previous_odometer')
    def _compute_distance_travelled(self):
        for record in self:
            if record.odometer and record.odometer > 0 and record.previous_odometer is not False:
                # Calculate the distance traveled (always non-negative)
                distance = record.odometer - record.previous_odometer
                record.distance_travelled = max(0, distance)  # Ensure non-negative
            else:
                record.distance_travelled = 0.0

    @api.onchange('vehicle_id', 'datetime')
    def _onchange_vehicle_id(self):
        if not self.vehicle_id or not self.vehicle_id.exists():
            return
            
        # Update the code to use datetime instead of date
        if self.datetime:
            previous_log = self.env['simply.fleet.fuel.log'].search([
                ('vehicle_id', '=', self.vehicle_id.id),
                ('datetime', '<', self.datetime),
                ('odometer', '>', 0)
            ], order='datetime desc, id desc', limit=1)
            
            if previous_log and previous_log.exists():
                self.previous_odometer = previous_log.odometer
            else:
                self.previous_odometer = self.vehicle_id.initial_odometer if self.vehicle_id.initial_odometer else 0.0

        if not self.fill_type:
            self.fill_type = 'full'

    @api.constrains('odometer', 'previous_odometer')
    def _check_odometer(self):
        for record in self:
            # Check that odometer is provided
            if not record.odometer or record.odometer <= 0:
                raise UserError(_('New odometer reading is required and must be greater than zero'))
                
            # The validation requiring odometer > previous_odometer has been removed
                
            # Check if previous odometer is zero (except for first entry)
            if record.previous_odometer == 0:
                # Check if this is really the first log for this vehicle
                previous_logs_count = self.env['simply.fleet.fuel.log'].search_count([
                    ('vehicle_id', '=', record.vehicle_id.id),
                    ('id', '!=', record._origin.id or False),
                ])
                
                if previous_logs_count > 0:
                    raise UserError(_('Previous odometer cannot be zero except for the first fuel log entry'))
                
    @api.constrains('liters')
    def _check_fuel_amount(self):
        for record in self:
            if not record.liters:
                raise UserError(_('Quantity is required. Please enter a value.'))
            elif record.liters <= 0:
                raise UserError(_('Quantity must be greater than zero'))

    @api.model
    def create(self, vals_list):
        # Check if vals_list is a dictionary (single record) or list (multiple records)
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
            
        # ... existing code ...
        
        records = super().create(vals_list)
        
        # Sync attachments after creation if needed
        for record in records:
            if 'attachment_ids' in vals:
                record._handle_attachment_sync()
                
        return records[0] if len(records) == 1 else records
