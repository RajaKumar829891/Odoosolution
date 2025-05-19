from odoo import models, fields, api
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class VehicleType(models.Model):
    _name = 'simply.fleet.vehicle.type'
    _description = 'Vehicle Type'
    _order = 'name'

    name = fields.Char(string='Type Name', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    
    def _compute_vehicle_count(self):
        for record in self:
            record.vehicle_count = self.env['simply.fleet.vehicle'].search_count([
                ('vehicle_type_id', '=', record.id)
            ])
    
    vehicle_count = fields.Integer(
        string='Vehicle Count',
        compute='_compute_vehicle_count'
    )

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'Vehicle Type Code must be unique!')
    ]

    def action_view_vehicles(self):
        """Action to view vehicles of this type."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vehicles',
            'res_model': 'simply.fleet.vehicle',
            'view_mode': 'tree,form',
            'domain': [('vehicle_type_id', '=', self.id)],
            'context': {'default_vehicle_type_id': self.id}
        }

class VehicleGroup(models.Model):
    _name = 'simply.fleet.vehicle.group'
    _description = 'Vehicle Group'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Group Name', required=True, tracking=True)
    ref = fields.Char(string='Reference', readonly=True, copy=False)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notes')
    vehicle_count = fields.Integer(string='Vehicle Count', compute='_compute_vehicle_count')
    vehicle_ids = fields.One2many('simply.fleet.vehicle', 'group_id', string='Vehicles')
    
    fleet_manager_ids = fields.Many2many(
        'hr.employee',
        'fleet_manager_group_rel',
        'vehicle_group_id',
        'employee_id',
        string='Fleet Managers',
        domain=[('is_fleet_manager', '=', True)],
        tracking=True,
        help='Managers responsible for this vehicle group'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('ref'):
                vals['ref'] = self.env['ir.sequence'].next_by_code('simply.fleet.vehicle.group')
        return super().create(vals_list)

    @api.depends('vehicle_ids')
    def _compute_vehicle_count(self):
        for group in self:
            group.vehicle_count = len(group.vehicle_ids)

    def action_view_vehicles(self):
        """Action to view vehicles in this group."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vehicles',
            'res_model': 'simply.fleet.vehicle',
            'view_mode': 'tree,form',
            'domain': [('group_id', '=', self.id)],
            'context': {'default_group_id': self.id}
        }

class Vehicle(models.Model):
    _name = 'simply.fleet.vehicle'
    _description = 'Vehicle Information'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # Basic Information
    name = fields.Char(string='Vehicle Name', required=True, tracking=True)
    vehicle_type_id = fields.Many2one(
        'simply.fleet.vehicle.type',
        string='Vehicle Type',
        required=True,
        tracking=True,
        help='Type of the vehicle'
    )
    ref = fields.Char(string='Reference', readonly=True, copy=False)
    model = fields.Char(string='Model', tracking=True)
    brand = fields.Char(string='Brand', tracking=True)
    year = fields.Integer(string='Year')
    chassis_number = fields.Char(string='Chassis Number')
    color = fields.Char(string='Color')
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notes')
    
    # Group and Management
    group_id = fields.Many2one(
        'simply.fleet.vehicle.group', 
        string='Vehicle Group', 
        tracking=True,
        help='Group this vehicle belongs to'
    )
    group_ref = fields.Char(
        related='group_id.ref', 
        string='Group Reference', 
        store=True, 
        readonly=True
    )
    fleet_manager_ids = fields.Many2many(
        related='group_id.fleet_manager_ids',
        string='Fleet Managers',
        readonly=True,
        help='Fleet Managers responsible for this vehicle'
    )
    driver_id = fields.Many2one(
        'hr.employee',
        string='Driver',
        tracking=True,
        domain=[('job_title', 'ilike', 'driver')],
        help='Assigned driver for this vehicle'
    )
    
    # Helper field - NEW ADDITION
    helper_id = fields.Many2one(
        'hr.employee',
        string='Helper',
        tracking=True,
        domain=[('job_title', 'ilike', 'helper')],
        help='Helper assigned to this vehicle'
    )
    
    # Show helper field - NEW ADDITION
    show_helper = fields.Boolean(
        string='Show Helper',
        compute='_compute_show_helper',
        store=True,
    )
    
    # Compute method for show_helper - NEW ADDITION
    @api.depends('vehicle_type_id')
    def _compute_show_helper(self):
        """Determine whether to show the helper field based on vehicle type"""
        for record in self:
            # Check if vehicle type has 'bus' in name or code (case insensitive)
            if record.vehicle_type_id and (
                (record.vehicle_type_id.code and 'bus' in record.vehicle_type_id.code.lower()) or
                (record.vehicle_type_id.name and 'bus' in record.vehicle_type_id.name.lower())
            ):
                record.show_helper = True
                _logger.info("Setting show_helper to True for vehicle %s with type %s", 
                            record.name, record.vehicle_type_id.name)
            else:
                record.show_helper = False
                _logger.info("Setting show_helper to False for vehicle %s with type %s", 
                            record.name, record.vehicle_type_id.name)
                # Clear the helper when vehicle type is not bus
                if record.helper_id:
                    record.helper_id = False
    
    # Debug onchange method - NEW ADDITION
    @api.onchange('vehicle_type_id')
    def _onchange_vehicle_type(self):
        """Debug helper to see what's happening with vehicle type"""
        if self.vehicle_type_id:
            # Log the vehicle type information for debugging
            _logger.info("Vehicle Type Selected: %s (code: %s)", 
                        self.vehicle_type_id.name, 
                        self.vehicle_type_id.code)
            # Force recompute of show_helper
            self._compute_show_helper()

    # Odometer and Fuel Information
    initial_odometer = fields.Float(
        string='Initial Odometer',
        tracking=True,
        help='Initial odometer reading when the vehicle was added to the fleet'
    )
    average_mileage = fields.Float(
        string='Set the mileage',
        help='Average mileage value in km/l or MPG',
        tracking=True
    )
    min_mileage = fields.Float(
    	string='Min Mileage',
    	help='Minimum expected mileage value in km/l or MPG',
    	tracking=True
    )

    max_mileage = fields.Float(
    	string='Max Mileage',
    	help='Maximum expected mileage value in km/l or MPG',
    	tracking=True
    )
    fuel_tank_capacity = fields.Float(
        string='Fuel Tank Capacity (L)',
        required=True,
        tracking=True,
        help='Total fuel tank capacity in liters'
    )
    average_efficiency = fields.Float(
        string='Average Fuel Efficiency (km/l)',
        compute='_compute_average_efficiency',
        store=True,
        help='Average fuel efficiency based on fuel logs'
    )

    # Status
    state = fields.Selection([
        ('active', 'Active'),
        ('maintenance', 'In Maintenance'),
        ('inactive', 'Inactive')
    ], string='Status', default='active', tracking=True)

    # Inspection Related Fields
    inspection_count = fields.Integer(
        compute='_compute_inspection_count',
        string='Inspections'
    )
    last_inspection_date = fields.Date(
        string='Last Inspection Date',
        compute='_compute_last_inspection',
        store=True
    )
    next_inspection_date = fields.Date(
        string='Next Scheduled Inspection',
        compute='_compute_next_inspection'
    )
    inspection_schedule_ids = fields.Many2many(
        'simply.fleet.inspection.schedule',
        'vehicle_inspection_schedule_rel',
        'vehicle_id',
        'schedule_id',
        string='Inspection Schedules'
    )
    last_inspection_odometer = fields.Float(
        string='Last Inspection Odometer',
        help='Odometer reading at last inspection'
    )

    # Counter fields for smart buttons
    document_count = fields.Integer(compute='_compute_document_count', string='Documents')
    fuel_log_count = fields.Integer(compute='_compute_fuel_log_count', string='Fuel Logs')
    battery_count = fields.Integer(compute='_compute_battery_count', string='Batteries')
    tyre_count = fields.Integer(compute='_compute_tyre_count', string='Tyres')
    active_tyre_count = fields.Integer(compute='_compute_tyre_count', string='Active Tyres')
    camera_count = fields.Integer(compute='_compute_camera_count', string='Cameras')
    asset_count = fields.Integer(compute='_compute_asset_count', string='Assets')
    image_count = fields.Integer(compute='_compute_image_count', string='Images')

    # Related Models
    asset_ids = fields.One2many(
        'simply.fleet.vehicle.asset',
        'vehicle_id',
        string='Assets',
        tracking=True
    )
    
    # Battery Information
    current_battery_id = fields.Many2one(
        'simply.fleet.battery',
        string='Current Battery',
        compute='_compute_current_battery',
        store=True
    )
    battery_health = fields.Float(
        related='current_battery_id.health_percentage',
        string='Current Battery Health',
        readonly=True
    )
    last_battery_maintenance_date = fields.Date(
        related='current_battery_id.last_inspection_date',
        string='Last Battery Inspection',
        readonly=True
    )

    # Compute Methods
    @api.depends('fuel_log_count')
    def _compute_average_efficiency(self):
        for record in self:
            fuel_logs = self.env['simply.fleet.fuel.log'].search([
                ('vehicle_id', '=', record.id),
                ('mileage', '>', 0)
            ])
            if fuel_logs:
                total_efficiency = sum(log.mileage for log in fuel_logs)
                record.average_efficiency = total_efficiency / len(fuel_logs)
            else:
                record.average_efficiency = 0.0

    def _compute_inspection_count(self):
        for record in self:
            record.inspection_count = self.env['simply.fleet.vehicle.inspection'].search_count([
                ('vehicle_id', '=', record.id)
            ])

    @api.depends('inspection_count')
    def _compute_last_inspection(self):
        for record in self:
            last_inspection = self.env['simply.fleet.vehicle.inspection'].search([
                ('vehicle_id', '=', record.id),
                ('state', 'in', ['completed', 'failed'])
            ], limit=1, order='inspection_date desc')
            record.last_inspection_date = last_inspection.inspection_date.date() if last_inspection else False

    def _compute_next_inspection(self):
        for record in self:
            next_schedule = self.env['simply.fleet.inspection.schedule'].search([
                ('vehicle_ids', 'in', record.id),
                ('active', '=', True),
                ('next_execution_date', '!=', False)
            ], limit=1, order='next_execution_date asc')
            record.next_inspection_date = next_schedule.next_execution_date if next_schedule else False

    def _compute_document_count(self):
        for record in self:
            record.document_count = self.env['simply.fleet.document'].search_count([
                ('vehicle_id', '=', record.id)
            ])

    def _compute_fuel_log_count(self):
        for record in self:
            record.fuel_log_count = self.env['simply.fleet.fuel.log'].search_count([
                ('vehicle_id', '=', record.id)
            ])
            
    def _compute_battery_count(self):
        for record in self:
            record.battery_count = self.env['simply.fleet.battery'].search_count([
                ('vehicle_id', '=', record.id)
            ])
            
    @api.depends('tyre_count')
    def _compute_tyre_count(self):
        for record in self:
            record.tyre_count = self.env['simply.fleet.tyre'].search_count([
                ('vehicle_id', '=', record.id)
            ])
            record.active_tyre_count = self.env['simply.fleet.tyre'].search_count([
                ('vehicle_id', '=', record.id),
                ('state', 'in', ['new', 'in_use']),
                ('active', '=', True)
            ])

    def _compute_camera_count(self):
        for record in self:
            record.camera_count = self.env['simply.fleet.camera'].search_count([
                ('vehicle_id', '=', record.id)
            ])

    def _compute_asset_count(self):
        for record in self:
            record.asset_count = self.env['simply.fleet.vehicle.asset'].search_count([
                ('vehicle_id', '=', record.id)
            ])
            
    def _compute_image_count(self):
        for record in self:
            record.image_count = self.env['simply.fleet.vehicle.image'].search_count([
                ('vehicle_id', '=', record.id)
            ])

    @api.depends('battery_count')
    def _compute_current_battery(self):
        for record in self:
            current_battery = self.env['simply.fleet.battery'].search([
                ('vehicle_id', '=', record.id),
                ('state', 'in', ['new', 'in_use']),
                ('active', '=', True)
            ], limit=1, order='installation_date desc')
            record.current_battery_id = current_battery.id if current_battery else False

    # CRUD Methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('ref'):
                vals['ref'] = self.env['ir.sequence'].next_by_code('simply.fleet.vehicle')
        return super().create(vals_list)

    # Action Methods
    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': 'Vehicle Documents',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'simply.fleet.document',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_fuel_logs(self):
        self.ensure_one()
        return {
            'name': 'Fuel Logs',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'simply.fleet.fuel.log',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
        
    def action_view_batteries(self):
        self.ensure_one()
        return {
            'name': 'Batteries',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'simply.fleet.battery',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
        
    def action_view_tyres(self):
        self.ensure_one()
        action = self.env.ref('simply_fleet.action_simply_fleet_tyre').read()[0]
        action.update({
            'domain': [('vehicle_id', '=', self.id)],
            'context': {
                'default_vehicle_id': self.id,
                'search_default_active': 1,
            },
            'name': f'Tyres - {self.name}',
            'target': 'current',
        })
        return action

    def action_view_cameras(self):
        self.ensure_one()
        return {
            'name': 'Cameras',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'simply.fleet.camera',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_assets(self):
        self.ensure_one()
        return {
            'name': 'Vehicle Assets',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'simply.fleet.vehicle.asset',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
        
    def action_view_images(self):
        self.ensure_one()
        return {
            'name': 'Vehicle Images',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'res_model': 'simply.fleet.vehicle.image',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_inspections(self):
        self.ensure_one()
        return {
            'name': 'Vehicle Inspections',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'simply.fleet.vehicle.inspection',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_schedule_inspection(self):
        """Quick action to schedule a new inspection"""
        self.ensure_one()
        return {
            'name': 'Schedule Inspection',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'simply.fleet.vehicle.inspection',
            'context': {
                'default_vehicle_id': self.id,
                'default_odometer': self.odometer,
            },
            'target': 'new',
        }

    def check_inspection_schedule(self):
        """Check if vehicle needs inspection based on schedules"""
        self.ensure_one()
        schedules = self.inspection_schedule_ids.filtered(lambda s: s.active)
        for schedule in schedules:
            if schedule.schedule_type in ['time', 'both']:
                if schedule.next_execution_date and schedule.next_execution_date <= fields.Date.today():
                    self._create_inspection_activity(schedule)
            
            if schedule.schedule_type in ['mileage', 'both']:
                if schedule.mileage_interval and (self.odometer - (self.last_inspection_odometer or 0)) >= schedule.mileage_interval:
                    self._create_inspection_activity(schedule)

    def _create_inspection_activity(self, schedule):
        """Create activity for due inspection"""
        activity_type_id = self.env.ref('mail.mail_activity_data_todo').id
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            note=f'Inspection due based on {schedule.name}',
            summary='Vehicle Inspection Required',
            user_id=self.env.user.id
        )

    def check_tyre_status(self):
        """Check tyre status and create activities for issues."""
        self.ensure_one()
        TyreModel = self.env['simply.fleet.tyre']
        
        # Check for worn tyres
        worn_tyres = TyreModel.search([
            ('vehicle_id', '=', self.id),
            ('state', '=', 'in_use'),
            ('current_tread_depth', '<', 2.0)  # Warning threshold
        ])
        
        if worn_tyres:
            # Create activity for worn tyres
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=f'Worn Tyres Need Attention',
                note=f'The following tyres have low tread depth: {", ".join(worn_tyres.mapped("name"))}',
                user_id=self.env.user.id
            )

        return True

    def action_check_maintenance_needs(self):
        """Check all maintenance needs for the vehicle"""
        self.ensure_one()
        
        # Check inspection schedules
        self.check_inspection_schedule()
        
        # Check tyre status
        self.check_tyre_status()
        
        # Check battery health
        if self.battery_health and self.battery_health < 70:  # Warning threshold
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                summary='Low Battery Health',
                note=f'Battery health is at {self.battery_health}%. Consider replacement.',
                user_id=self.env.user.id
            )

        return True
