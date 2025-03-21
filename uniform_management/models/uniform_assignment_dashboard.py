from odoo import models, api, fields
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class UniformAssignment(models.Model):
    _inherit = 'uniform.assignment'
    
    @api.model
    def get_dashboard_data(self):
        """
        Get data for the uniform management dashboard
        """
        # Get statistics
        total_assigned = self.search_count([('state', 'in', ['assigned', 'partially_returned'])])
        
        # Get pending returns (expected return date is in the past)
        today = fields.Date.today()
        pending_returns = self.search_count([
            ('state', 'in', ['assigned', 'partially_returned']),
            ('expected_return_date', '<', today)
        ])
        
        # Get items low in stock
        items_low_in_stock = self.env['uniform.item'].search_count([
            ('qty_available', '<=', 'min_qty')
        ])
        
        # Get category distribution data
        categories = self.env['uniform.assignment'].read_group(
            [('state', 'in', ['assigned', 'partially_returned'])],
            ['category', 'quantity:sum'],
            ['category']
        )
        
        category_labels = []
        category_values = []
        for category in categories:
            if category['category']:
                # Get display name for category
                category_name = dict(self._fields['category'].selection).get(category['category'])
                category_labels.append(category_name)
                category_values.append(category['quantity'])
        
        # Get monthly assignment data for the last 6 months
        month_data = []
        for i in range(5, -1, -1):
            start_date = datetime.today() + relativedelta(months=-i, day=1)
            end_date = datetime.today() + relativedelta(months=-i+1, day=1, days=-1)
            
            count = self.search_count([
                ('assignment_date', '>=', start_date.strftime('%Y-%m-%d')),
                ('assignment_date', '<=', end_date.strftime('%Y-%m-%d'))
            ])
            
            month_data.append({
                'label': start_date.strftime('%b %Y'),
                'value': count
            })
        
        # Get recent assignments
        recent_assignments = self.search([
            ('assignment_date', '>=', (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
        ], limit=10, order='assignment_date desc')
        
        recent_assignment_data = []
        for assignment in recent_assignments:
            recent_assignment_data.append({
                'name': assignment.name,
                'employee_name': assignment.employee_id.name,
                'item_name': assignment.item_id.name,
                'date': assignment.assignment_date.strftime('%Y-%m-%d'),
                'state': assignment.state,
                'state_label': dict(self._fields['state'].selection).get(assignment.state)
            })
            
        return {
            'stats': {
                'total_assigned': total_assigned,
                'pending_returns': pending_returns,
                'low_stock_items': items_low_in_stock
            },
            'category_data': {
                'labels': category_labels,
                'values': category_values
            },
            'monthly_data': {
                'labels': [item['label'] for item in month_data],
                'values': [item['value'] for item in month_data]
            },
            'recent_assignments': recent_assignment_data
        }
