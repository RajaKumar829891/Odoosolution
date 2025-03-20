# hooks.py
from odoo import api, SUPERUSER_ID

def post_init_hook(env_or_cr, registry=None):
    """Post init hook that works with both (cr, registry) and (env) signatures"""
    if registry is None:
        env = env_or_cr
        cr = env.cr
    else:
        cr = env_or_cr
        env = api.Environment(cr, SUPERUSER_ID, {})
    
    try:
        # Create default transaction types
        if 'simply_fleet.transaction.type' in env:
            default_transaction_types = [
                {'name': 'Fuel Fill', 'description': 'Regular fuel filling transaction', 'active': True},
                {'name': 'Maintenance', 'description': 'Vehicle maintenance and repairs', 'active': True},
                {'name': 'Insurance', 'description': 'Insurance premium payments', 'active': True},
                {'name': 'Toll', 'description': 'Toll payments', 'active': True},
                {'name': 'Fine', 'description': 'Traffic violation fines', 'active': True},
            ]
            
            TransactionType = env['simply_fleet.transaction.type']
            for type_data in default_transaction_types:
                if not TransactionType.search([('name', '=', type_data['name'])]):
                    TransactionType.create(type_data)
            
        cr.commit()

    except Exception as e:
        cr.rollback()
        raise e
