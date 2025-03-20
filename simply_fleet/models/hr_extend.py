from odoo import models, fields, api

class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    is_fleet_manager = fields.Boolean(
        string='Is Fleet Manager',
        default=False,
        help='Check if employee is a fleet manager'
    )
    
    managed_vehicle_groups_ids = fields.Many2many(
        'simply.fleet.vehicle.group',
        'fleet_manager_group_rel',
        'employee_id',
        'vehicle_group_id',
        string='Managed Vehicle Groups',
        help='Vehicle groups managed by this employee'
    )

    managed_vehicle_count = fields.Integer(
        string='Managed Vehicles',
        compute='_compute_managed_vehicle_count'
    )

    managed_vehicle_ids = fields.Many2many(
        'simply.fleet.vehicle',
        string='Managed Vehicles',
        compute='_compute_managed_vehicles'
    )

    @api.depends('managed_vehicle_groups_ids')
    def _compute_managed_vehicle_count(self):
        for employee in self:
            count = 0
            if employee.managed_vehicle_groups_ids:
                count = self.env['simply.fleet.vehicle'].search_count([
                    ('group_id', 'in', employee.managed_vehicle_groups_ids.ids)
                ])
            employee.managed_vehicle_count = count

    @api.depends('managed_vehicle_groups_ids')
    def _compute_managed_vehicles(self):
        for employee in self:
            if employee.managed_vehicle_groups_ids:
                employee.managed_vehicle_ids = self.env['simply.fleet.vehicle'].search([
                    ('group_id', 'in', employee.managed_vehicle_groups_ids.ids)
                ])
            else:
                employee.managed_vehicle_ids = False

    def action_view_managed_vehicles(self):
        self.ensure_one()
        return {
            'name': 'Managed Vehicles',
            'type': 'ir.actions.act_window',
            'res_model': 'simply.fleet.vehicle',
            'view_mode': 'tree,form',
            'domain': [('group_id', 'in', self.managed_vehicle_groups_ids.ids)],
            'context': {
                'default_group_id': self.managed_vehicle_groups_ids[0].id if self.managed_vehicle_groups_ids else False,
                'search_default_group_by_group': 1
            },
        }
