# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api


class UniformAssignmentReport(models.Model):
    _name = 'uniform.assignment.report'
    _description = 'Uniform Assignment Analysis Report'
    _auto = False
    _order = 'assignment_date desc'

    name = fields.Char('Reference', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    job_id = fields.Many2one('hr.job', string='Job Position', readonly=True)
    item_id = fields.Many2one('uniform.item', string='Uniform Item', readonly=True)
    type_id = fields.Many2one('uniform.type', string='Uniform Type', readonly=True)
    category = fields.Selection([
        ('tshirt', 'T-Shirt'),
        ('pants', 'Pants'),
        ('shoes', 'Shoes'),
        ('belt', 'Belt'),
        ('jacket', 'Jacket'),
        ('cap', 'Cap'),
        ('other', 'Other'),
    ], string='Category', readonly=True)
    size_id = fields.Many2one('uniform.size', string='Size', readonly=True)
    assignment_date = fields.Date('Assignment Date', readonly=True)
    expected_return_date = fields.Date('Expected Return Date', readonly=True)
    quantity = fields.Integer('Assigned Quantity', readonly=True)
    returned_qty = fields.Integer('Returned Quantity', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('partially_returned', 'Partially Returned'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ], string='Status', readonly=True)
    
    def _select(self):
        select_str = """
            SELECT
                a.id,
                a.name,
                a.employee_id,
                e.department_id,
                e.job_id,
                a.item_id,
                a.type_id,
                a.category,
                a.size_id,
                a.assignment_date,
                a.expected_return_date,
                a.quantity,
                a.returned_qty,
                a.state
        """
        return select_str

    def _from(self):
        from_str = """
            FROM uniform_assignment a
            LEFT JOIN hr_employee e ON a.employee_id = e.id
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY
                a.id,
                a.name,
                a.employee_id,
                e.department_id,
                e.job_id,
                a.item_id,
                a.type_id,
                a.category,
                a.size_id,
                a.assignment_date,
                a.expected_return_date,
                a.quantity,
                a.returned_qty,
                a.state
        """
        return group_by_str

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s as (
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._group_by())
        )
