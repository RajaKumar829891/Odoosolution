from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class VehicleInspection(models.Model):
    _name = 'simply.fleet.vehicle.inspection'
    _description = 'Vehicle Inspection'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'inspection_date desc'

    name = fields.Char(string='Reference', required=True, copy=False, 
                      readonly=True, default='New', tracking=True)
    vehicle_id = fields.Many2one('simply.fleet.vehicle', string='Vehicle', required=True, tracking=True)
    inspection_template_id = fields.Many2one('simply.fleet.inspection.template', 
                                           string='Inspection Template', tracking=True)
    inspection_date = fields.Datetime(string='Inspection Date', 
                                    default=fields.Datetime.now, required=True, tracking=True)
    inspector_id = fields.Many2one('res.users', string='Inspector', 
                                  default=lambda self: self.env.user, tracking=True)
    
    # Overall Status - Removed 'failed' option
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], string='Status', default='draft', tracking=True)

    # Inspection Categories and Checklist
    inspection_line_ids = fields.One2many(
        'simply.fleet.vehicle.inspection.line', 
        'inspection_id', 
        string='Inspection Lines',
        tracking=True
    )

    # Summary Fields
    total_issues = fields.Integer(compute='_compute_issues', store=True)
    critical_issues = fields.Integer(compute='_compute_issues', store=True)
    notes = fields.Text(string='Additional Notes', tracking=True)
    
    # Mileage at Inspection
    odometer = fields.Float(string='Odometer Reading', tracking=True)
    odometer_unit = fields.Selection([
        ('kilometers', 'Kilometers'),
        ('miles', 'Miles')
    ], string='Odometer Unit', default='kilometers', tracking=True)

    # Documents and Images
    inspection_document_ids = fields.Many2many(
        'ir.attachment', 
        'vehicle_inspection_attachment_rel',
        'inspection_id',
        'attachment_id',
        string='Documents'
    )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'simply.fleet.vehicle.inspection'
            ) or 'New'
        
        # If template is provided during creation, prepare inspection lines
        template_id = vals.get('inspection_template_id')
        if template_id:
            template = self.env['simply.fleet.inspection.template'].browse(template_id)
            lines = []
            for template_line in template.template_line_ids:
                lines.append((0, 0, {
                    'sequence': template_line.sequence,
                    'category': template_line.category,
                    'component': template_line.component,
                    'priority': template_line.default_priority,
                    'description': template_line.instructions
                }))
            vals['inspection_line_ids'] = lines
            
        return super(VehicleInspection, self).create(vals)

    def write(self, vals):
        # If template is changed through write method, handle line updates
        if 'inspection_template_id' in vals and self.state == 'draft':
            template_id = vals['inspection_template_id']
            if template_id:
                template = self.env['simply.fleet.inspection.template'].browse(template_id)
                lines = [(5, 0, 0)]  # Clear existing lines
                for template_line in template.template_line_ids:
                    lines.append((0, 0, {
                        'sequence': template_line.sequence,
                        'category': template_line.category,
                        'component': template_line.component,
                        'priority': template_line.default_priority,
                        'description': template_line.instructions
                    }))
                vals['inspection_line_ids'] = lines
        
        return super(VehicleInspection, self).write(vals)

    @api.depends('inspection_line_ids', 'inspection_line_ids.status')
    def _compute_issues(self):
        for record in self:
            issues = record.inspection_line_ids.filtered(lambda x: x.status in ['issue', 'critical'])
            record.total_issues = len(issues)
            record.critical_issues = len(record.inspection_line_ids.filtered(
                lambda x: x.status == 'critical'
            ))

    @api.onchange('inspection_template_id')
    def _onchange_inspection_template(self):
        """When template is changed, load its items into inspection lines"""
        if self.inspection_template_id and self.state == 'draft':
            # Clear existing lines
            self.inspection_line_ids = [(5, 0, 0)]
            
            # Create new lines from template
            lines = []
            for template_line in self.inspection_template_id.template_line_ids:
                lines.append((0, 0, {
                    'sequence': template_line.sequence,
                    'category': template_line.category,
                    'component': template_line.component,
                    'priority': template_line.default_priority,
                    'description': template_line.instructions
                }))
            self.inspection_line_ids = lines

    def action_start_inspection(self):
        """Start the inspection process"""
        if not self.inspection_line_ids and self.inspection_template_id:
            self.load_template_items()
        self.write({'state': 'in_progress'})

    def action_complete_inspection(self):
        """Complete the inspection"""
        if not self.inspection_line_ids:
            raise UserError(_('You cannot complete an inspection without any inspection items.'))
        
        # Check if all inspection lines have a status
        incomplete_lines = self.inspection_line_ids.filtered(lambda x: not x.status)
        if incomplete_lines:
            raise UserError(_('Please complete all inspection items before completing the inspection.'))
            
        # Simply mark as completed regardless of critical issues
        self.write({'state': 'completed'})

    def action_reset_to_draft(self):
        """Reset inspection to draft state"""
        self.write({'state': 'draft'})

    def load_template_items(self):
        """Load inspection items from the selected template"""
        self.ensure_one()
        if not self.inspection_template_id:
            raise UserError(_('Please select an inspection template first.'))
        
        # Clear existing lines
        self.inspection_line_ids.unlink()
        
        # Create new lines from template
        for template_line in self.inspection_template_id.template_line_ids:
            self.env['simply.fleet.vehicle.inspection.line'].create({
                'inspection_id': self.id,
                'sequence': template_line.sequence,
                'category': template_line.category,
                'component': template_line.component,
                'priority': template_line.default_priority,
                'description': template_line.instructions
            })
        
        return True


class VehicleInspectionLine(models.Model):
    _name = 'simply.fleet.vehicle.inspection.line'
    _description = 'Vehicle Inspection Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    inspection_id = fields.Many2one('simply.fleet.vehicle.inspection', 
                                  string='Inspection', required=True, 
                                  ondelete='cascade')
    category = fields.Selection([
        ('exterior', 'Exterior'),
        ('interior', 'Interior'),
        ('engine', 'Engine'),
        ('transmission', 'Transmission'),
        ('brakes', 'Brakes'),
        ('tires', 'Tires'),
        ('electrical', 'Electrical'),
        ('safety', 'Safety Equipment'),
        ('other', 'Other')
    ], string='Category', required=True)

    component = fields.Char(string='Component', required=True)
    status = fields.Selection([
        ('ok', 'OK'),
        ('issue', 'Issue Found'),
        ('critical', 'Critical Issue'),
        ('na', 'Not Applicable')
    ], string='Status', required=True)
    
    description = fields.Text(string='Description')
    recommended_action = fields.Text(string='Recommended Action')
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Critical')
    ], string='Priority', default='1')
    
    estimated_cost = fields.Float(string='Estimated Cost')

    # Updated image field without compute fields
    inspection_image_ids = fields.Many2many(
        'ir.attachment',
        'inspection_line_image_rel',
        'inspection_line_id',
        'attachment_id',
        string='Inspection Images',
        domain=[('mimetype', 'ilike', 'image/')],
    )

    @api.onchange('status')
    def _onchange_status(self):
        """Update priority based on status"""
        if self.status == 'critical':
            self.priority = '3'
        elif self.status == 'issue':
            self.priority = '2'
        elif self.status == 'ok':
            self.priority = '1'


class VehicleInspectionTemplate(models.Model):
    _name = 'simply.fleet.inspection.template'
    _description = 'Vehicle Inspection Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Template Name', required=True, tracking=True)
    description = fields.Text(string='Description', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    
    template_line_ids = fields.One2many(
        'simply.fleet.inspection.template.line',
        'template_id',
        string='Inspection Items',
        tracking=True
    )

    def toggle_active(self):
        """Toggle the active state"""
        for record in self:
            record.active = not record.active

    def create_inspection(self, vehicle_id, scheduled_date=None):
        """Create a new inspection from this template"""
        inspection_obj = self.env['simply.fleet.vehicle.inspection']
        
        inspection = inspection_obj.create({
            'vehicle_id': vehicle_id,
            'inspection_template_id': self.id,
            'inspection_date': scheduled_date or fields.Datetime.now(),
        })
        
        inspection.load_template_items()
        return inspection


class VehicleInspectionTemplateLine(models.Model):
    _name = 'simply.fleet.inspection.template.line'
    _description = 'Vehicle Inspection Template Line'
    _order = 'sequence, id'
    
    template_id = fields.Many2one('simply.fleet.inspection.template', 
                                string='Template', required=True,
                                ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    category = fields.Selection([
        ('exterior', 'Exterior'),
        ('interior', 'Interior'),
        ('engine', 'Engine'),
        ('transmission', 'Transmission'),
        ('brakes', 'Brakes'),
        ('tires', 'Tires'),
        ('electrical', 'Electrical'),
        ('safety', 'Safety Equipment'),
        ('other', 'Other')
    ], required=True)
    component = fields.Char(required=True)
    instructions = fields.Text()
    default_priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Critical')
    ], default='1')


class VehicleInspectionSchedule(models.Model):
    _name = 'simply.fleet.inspection.schedule'
    _description = 'Vehicle Inspection Schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    template_id = fields.Many2one(
        'simply.fleet.inspection.template',
        string='Inspection Template',
        required=True,
        tracking=True
    )
    vehicle_ids = fields.Many2many(
        'simply.fleet.vehicle',
        'fleet_vehicle_inspection_schedule_rel',
        'schedule_id',
        'vehicle_id',
        string='Vehicles',
        tracking=True
    )
    
    schedule_type = fields.Selection([
        ('mileage', 'Based on Mileage'),
        ('time', 'Based on Time'),
        ('both', 'Both Mileage and Time')
    ], required=True, default='time', tracking=True)
    
    interval_number = fields.Integer(string='Repeat Every', default=1, tracking=True)
    interval_type = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years'),
    ], string='Interval Unit', default='months', tracking=True)
    
    mileage_interval = fields.Float(string='Mileage Interval', tracking=True)
    next_execution_date = fields.Date(string='Next Scheduled Date', tracking=True)
    last_execution_date = fields.Date(string='Last Execution Date', tracking=True)

    def toggle_active(self):
        """Toggle the active state"""
        for record in self:
            record.active = not record.active

    @api.model
    def _cron_generate_inspections(self):
        """Cron job to generate scheduled inspections"""
        schedules = self.search([('active', '=', True)])
        for schedule in schedules:
            schedule._generate_due_inspections()

    def _generate_due_inspections(self):
        """Generate inspections for vehicles that are due"""
        today = fields.Date.today()
        
        for vehicle in self.vehicle_ids:
            create_inspection = False
            
            # Check time-based schedule
            if self.schedule_type in ['time', 'both']:
                if not self.last_execution_date or \
                   self.next_execution_date <= today:
                    create_inspection = True
            
            # Check mileage-based schedule
            if self.schedule_type in ['mileage', 'both'] and \
               self.mileage_interval > 0:
                last_odometer = vehicle.odometer or 0
                if (last_odometer - (vehicle.last_inspection_odometer or 0)) >= \
                   self.mileage_interval:
                    create_inspection = True
            
            if create_inspection:
                # Create inspection from template
                inspection = self.template_id.create_inspection(
                    vehicle.id,
                    fields.Datetime.now()
                )
                
                # Update schedule records
                self.write({
                    'last_execution_date': today,
                    'next_execution_date': self._calculate_next_date()
                })
                
                # Update vehicle record
                vehicle.write({
                    'last_inspection_odometer': vehicle.odometer
                })

    def _calculate_next_date(self):
        """Calculate the next execution date based on interval settings"""
        if not self.interval_number:
            return False
        
        last_date = self.last_execution_date or fields.Date.today()
        
        if self.interval_type == 'days':
            next_date = last_date + relativedelta(days=self.interval_number)
        elif self.interval_type == 'weeks':
            next_date = last_date + relativedelta(weeks=self.interval_number)
        elif self.interval_type == 'months':
            next_date = last_date + relativedelta(months=self.interval_number)
        elif self.interval_type == 'years':
            next_date = last_date + relativedelta(years=self.interval_number)
            
        return next_date

    def action_schedule_inspections(self):
        """Manually trigger inspection generation for this schedule"""
        self.ensure_one()
        self._generate_due_inspections()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Inspection Generation'),
                'message': _('Inspections have been generated based on the schedule.'),
                'sticky': False,
                'type': 'success',
            }
        }
        """Calculate the next execution date based on interval settings"""
