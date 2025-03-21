{
    'name': 'Employee Uniform Management',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Manage employee uniforms and accessories',
    'description': """
        This module allows you to manage employee uniforms including:
        - T-shirts, pants, shoes, belts and other accessories
        - Tracking of uniform assignments with dates
        - Size management for different uniform items
        - Return tracking
        - Reports for uniform distribution
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['hr'],
    'data': [
        'security/uniform_security.xml',
        'security/ir.model.access.csv',
        'data/uniform_type_data.xml',
        'data/uniform_item_data.xml',
        'data/uniform_size_data.xml',
        'views/uniform_item_views.xml',
        'views/uniform_assignment_views.xml',
        'views/uniform_type_views.xml',
        'views/uniform_size_views.xml',
        'views/uniform_return_views.xml',
        'views/hr_employee_views.xml',
        'views/menu_views.xml',
        'wizard/views/mass_assignment_view.xml',
        'report/uniform_assignment_report_template.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
