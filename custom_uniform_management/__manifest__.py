{
    'name': 'Custom Uniform Management System',
    'version': '1.0',
    'summary': 'Manage employee uniforms and inventory',
    'description': """
        This module adds the following features:
        - Uniform types and sizes management
        - Uniform assignment to employees
        - Uniform return tracking
        - Integration with inventory module
        - Mass uniform assignment capability
    """,
    'category': 'Human Resources/Employees',
    'author': 'Your Company',
    'website': 'https://www.example.com',
    'depends': ['hr', 'stock', 'product', 'mail'],
    'data': [
        'security/uniform_security.xml',
        'security/ir.model.access.csv',
        'data/uniform_sequences.xml',
        'wizard/mass_uniform_assignment_views.xml',  # Load wizard views first
        'views/product_views.xml',
        'views/uniform_assignment_views.xml',
        'views/uniform_return_views.xml',
        'views/uniform_menus.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
