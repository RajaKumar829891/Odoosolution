from odoo import api, fields, models, _

class FleetDriverAssignWizard(models.TransientModel):
    _name = 'fleet.driver.assign.wizard'
    _description = 'Assign Driver to Booking'
    
    booking_id = fields.Many2one(
        'fleet.booking', 
        string='Booking', 
        required=True,
        ondelete='cascade'
    )
    driver_id = fields.Many2one(
        'fleet.driver', 
        string='Driver', 
        required=True,
        domain=[('state', '=', 'available')],
        ondelete='cascade'
    )
    employee_id = fields.Many2one('hr.employee', string='Employee', compute='_compute_employee_data', store=False)
    
    # Additional employee-related fields
    employee_department = fields.Char(string='Department', compute='_compute_employee_data', store=False)
    employee_job = fields.Char(string='Job Position', compute='_compute_employee_data', store=False)
    employee_work_phone = fields.Char(string='Work Phone', compute='_compute_employee_data', store=False)
    employee_work_email = fields.Char(string='Work Email', compute='_compute_employee_data', store=False)
    
    note = fields.Text(string='Assignment Note')
    
    @api.depends('driver_id')
    def _compute_employee_data(self):
        for record in self:
            if record.driver_id and record.driver_id.employee_id:
                record.employee_id = record.driver_id.employee_id
                record.employee_department = record.driver_id.employee_id.department_id.name if record.driver_id.employee_id.department_id else False
                record.employee_job = record.driver_id.employee_id.job_id.name if record.driver_id.employee_id.job_id else False
                record.employee_work_phone = record.driver_id.employee_id.work_phone or False
                record.employee_work_email = record.driver_id.employee_id.work_email or False
            else:
                record.employee_id = False
                record.employee_department = False
                record.employee_job = False
                record.employee_work_phone = False
                record.employee_work_email = False
    
    def action_assign(self):
        self.ensure_one()
        if self.driver_id and self.booking_id:
            self.booking_id.write({
                'driver_id': self.driver_id.id,
            })
            # Update driver status
            self.driver_id.action_set_on_trip()
            # Create a note in the chatter
            if self.note:
                self.booking_id.message_post(body=_("Driver %s assigned: %s") % 
                                           (self.driver_id.name, self.note))
            else:
                self.booking_id.message_post(body=_("Driver %s assigned to this booking.") % 
                                           self.driver_id.name)
        return {'type': 'ir.actions.act_window_close'}