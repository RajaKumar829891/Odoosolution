# File: fleet_booking/wizards/import_simply_fleet_vehicles.py
from odoo import api, fields, models, _

class ImportSimplyFleetVehicles(models.TransientModel):
    _name = 'fleet.import.simply.vehicles.wizard'
    _description = 'Import Simply Fleet Vehicles'
    
    vehicle_ids = fields.Many2many(
        'simply.fleet.vehicle', 
        string='Simply Fleet Vehicles',
        domain=[('active', '=', True)],
        required=True,
    )
    
    def action_import_vehicles(self):
        FleetVehicle = self.env['fleet.vehicle']
        imported_count = 0
        
        for vehicle in self.vehicle_ids:
            # Check if vehicle already imported
            existing = FleetVehicle.search([
                ('simply_fleet_vehicle_id', '=', vehicle.id)
            ], limit=1)
            
            if existing:
                continue
                
            # Create new fleet booking vehicle with default values for required fields
            vals = {
                'simply_fleet_vehicle_id': vehicle.id,
                'name': vehicle.name,
                'license_plate': vehicle.ref or '',
                'vin': vehicle.chassis_number or '',
                'model': vehicle.model or '',
                'make': vehicle.brand or '',
                'color': vehicle.color or '',
                'active': vehicle.active,
                'passenger_capacity': 4,  # Default passenger capacity
                'vehicle_type': 'sedan',  # Default vehicle type - REQUIRED
            }
            
            # Map vehicle type based on vehicle_type_id name
            if vehicle.vehicle_type_id:
                vehicle_type_name = vehicle.vehicle_type_id.name.lower() if vehicle.vehicle_type_id.name else ''
                
                # More specific mappings based on type name
                if '17' in vehicle_type_name and 'traveller' in vehicle_type_name:
                    vals['vehicle_type'] = '17_seater_luxury_force_traveller'
                    vals['passenger_capacity'] = 17
                elif '26' in vehicle_type_name and 'traveller' in vehicle_type_name:
                    vals['vehicle_type'] = '26_seater_luxury_force_traveller'
                    vals['passenger_capacity'] = 26
                elif '33' in vehicle_type_name and 'coach' in vehicle_type_name:
                    vals['vehicle_type'] = '33_seater_super_luxury_recliner_ac_coach'
                    vals['passenger_capacity'] = 33
                elif '41' in vehicle_type_name and 'coach' in vehicle_type_name:
                    vals['vehicle_type'] = '41_seater_super_luxury_recliner_ac_coach'
                    vals['passenger_capacity'] = 41
                elif '48' in vehicle_type_name and 'coach' in vehicle_type_name:
                    vals['vehicle_type'] = '48_seater_luxury_ac_coach'
                    vals['passenger_capacity'] = 48
                elif '49' in vehicle_type_name and 'coach' in vehicle_type_name:
                    vals['vehicle_type'] = '49_seater_super_luxury_ac_coach_2024'
                    vals['passenger_capacity'] = 49
                elif '50' in vehicle_type_name and 'coach' in vehicle_type_name:
                    vals['vehicle_type'] = '50_seater_super_luxury_ac_coach_2025'
                    vals['passenger_capacity'] = 50
                elif 'innova' in vehicle_type_name:
                    if 'crysta' in vehicle_type_name:
                        vals['vehicle_type'] = 'toyota_innova_crysta'
                    else:
                        vals['vehicle_type'] = 'toyota_innova'
                    vals['passenger_capacity'] = 7
                elif 'ertiga' in vehicle_type_name:
                    vals['vehicle_type'] = 'ertiga'
                    vals['passenger_capacity'] = 7
                elif 'amaze' in vehicle_type_name:
                    vals['vehicle_type'] = 'honda_amaze'
                    vals['passenger_capacity'] = 5
                elif 'aura' in vehicle_type_name:
                    vals['vehicle_type'] = 'hyundai_aura'
                    vals['passenger_capacity'] = 5
                elif 'xcent' in vehicle_type_name:
                    vals['vehicle_type'] = 'hyundai_xcent'
                    vals['passenger_capacity'] = 5
                elif 'tavera' in vehicle_type_name:
                    vals['vehicle_type'] = 'tavera'
                    vals['passenger_capacity'] = 8
                # Fallback to more generic types
                elif 'bus' in vehicle_type_name:
                    if 'mini' in vehicle_type_name:
                        vals['vehicle_type'] = 'mini_bus'
                        vals['passenger_capacity'] = 15
                    else:
                        vals['vehicle_type'] = 'bus'
                        vals['passenger_capacity'] = 40
                elif 'sedan' in vehicle_type_name:
                    vals['vehicle_type'] = 'sedan'
                    vals['passenger_capacity'] = 4
                elif 'suv' in vehicle_type_name:
                    vals['vehicle_type'] = 'suv'
                    vals['passenger_capacity'] = 7
                elif 'coach' in vehicle_type_name:
                    vals['vehicle_type'] = '26_seater_ac_coach'
                    vals['passenger_capacity'] = 26
            
            # Set state
            simply_state = vehicle.state
            if simply_state == 'active':
                vals['state'] = 'available'
            elif simply_state == 'maintenance':
                vals['state'] = 'maintenance'
            elif simply_state == 'inactive':
                vals['state'] = 'out_of_service'
            
            # Set odometer
            vals['current_odometer'] = vehicle.initial_odometer or 0.0
            
            # Create the vehicle
            FleetVehicle.create(vals)
            imported_count += 1
        
        # Show success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Import Successful'),
                'message': _('%s vehicles have been imported successfully.') % imported_count,
                'sticky': False,
                'type': 'success',
            }
        }