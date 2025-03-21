from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

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
        string='Attachments'
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
        string='Liters', 
        tracking=True,
        required=True
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
    
    def _sync_ir_attachments(self):
        """Synchronize mail attachments with custom attachment field"""
        for record in self:
            # Find all attachments linked to this record via mail.thread
            mail_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id)
            ])
            
            # Link them to our custom field if not already linked
            if mail_attachments:
                record.attachment_ids = mail_attachments
    
    # Override write to sync attachments
    def write(self, vals):
        result = super().write(vals)
        # If attachment_ids was updated, sync back to ir.attachment
        if 'attachment_ids' in vals:
            self._sync_ir_attachments()
        return result
    
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
            # Format the time as HH:MM:SS
                record.time_display = record.datetime.strftime('%H:%M:%S:%')
            else:
                record.time_display = Falsee

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
            # Include both date and formatted time
                record.display_date = record.datetime.date()
            # Create a new field for the formatted datetime
                record.datetime_display = record.datetime.strftime('%I:%M:%S %p')
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
            record.show_transaction_type = bool(record.station_type == 'petrol_pump')

    @api.onchange('station_type')
    def _onchange_station_type(self):
        if self.station_type == 'diesel_tanker':
            self.transaction_type_id = False

    @api.depends('distance_travelled', 'liters', 'fill_type')
    def _compute_mileage(self):
        for record in self:
            if record.fill_type == 'full' and record.liters and record.liters > 0 and record.distance_travelled:
                record.mileage = record.distance_travelled / record.liters
            else:
                record.mileage = 0.0

    @api.depends('liters', 'price_per_liter')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = (record.liters or 0.0) * (record.price_per_liter or 0.0)

    @api.depends('vehicle_id', 'date')
    def _compute_previous_odometer(self):
        for record in self:
            if not record.vehicle_id or not record.vehicle_id.exists():
                record.previous_odometer = 0.0
                continue
            
            try:
                if record.date:
                    previous_log = self.env['simply.fleet.fuel.log'].search([
                        ('vehicle_id', '=', record.vehicle_id.id),
                        ('date', '<', record.date),
                        ('id', '!=', record._origin.id or False),
                        ('odometer', '!=', False)
                    ], order='datetime desc, id desc', limit=1)
                    
                    if previous_log and previous_log.exists():
                        record.previous_odometer = previous_log.odometer
                    else:
                        record.previous_odometer = record.vehicle_id.initial_odometer if record.vehicle_id.initial_odometer else 0.0
                else:
                    record.previous_odometer = 0.0
            except Exception:
                record.previous_odometer = 0.0

    @api.depends('odometer', 'previous_odometer')
    def _compute_distance_travelled(self):
        for record in self:
            if record.odometer and record.previous_odometer:
                record.distance_travelled = record.odometer - record.previous_odometer
            else:
                record.distance_travelled = 0.0

    @api.onchange('vehicle_id', 'datetime')
    def _onchange_vehicle_id(self):
        if not self.vehicle_id or not self.vehicle_id.exists():
            return
            
        if self.date:  # Using computed date from datetime
            previous_log = self.env['simply.fleet.fuel.log'].search([
                ('vehicle_id', '=', self.vehicle_id.id),
                ('date', '<', self.date),
                ('odometer', '!=', False)
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
            if record.odometer and record.previous_odometer and record.odometer < record.previous_odometer:
                raise UserError('New odometer reading cannot be less than previous reading')

    @api.constrains('liters')
    def _check_fuel_amount(self):
        for record in self:
            if record.liters and record.liters <= 0:
                raise UserError('Fuel amount must be greater than zero')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('simply.fleet.fuel.log')
        return super().create(vals_list)
