# File: fleet_booking/models/fleet_vehicle_bridge.py
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class FleetVehicleBridge(models.Model):
    _inherit = 'fleet.vehicle'
    
    # Add relationship to simply.fleet.vehicle
    simply_fleet_vehicle_id = fields.Many2one(
        'simply.fleet.vehicle', 
        string='Simply Fleet Vehicle',
        ondelete='restrict',
        help='Link to the vehicle in Simply Fleet module'
    )
    
    # Override fields that should be synchronized
    @api.onchange('simply_fleet_vehicle_id')
    def _onchange_simply_fleet_vehicle_id(self):
        if self.simply_fleet_vehicle_id:
            # Map Simply Fleet vehicle fields to Fleet Booking vehicle fields
            self.name = self.simply_fleet_vehicle_id.name
            self.license_plate = self.simply_fleet_vehicle_id.ref or ''
            self.vin = self.simply_fleet_vehicle_id.chassis_number or ''
            self.model = self.simply_fleet_vehicle_id.model or ''
            self.make = self.simply_fleet_vehicle_id.brand or ''
            self.color = self.simply_fleet_vehicle_id.color or ''
            
            # Set default values for required fields
            self.passenger_capacity = 4  # Default passenger capacity
            self.vehicle_type = 'sedan'  # Default vehicle type
            
            # Map vehicle type based on vehicle_type_id name
            if self.simply_fleet_vehicle_id.vehicle_type_id:
                vehicle_type_name = self.simply_fleet_vehicle_id.vehicle_type_id.name.lower() if self.simply_fleet_vehicle_id.vehicle_type_id.name else ''
                
                # More specific mappings based on type name
                if '17' in vehicle_type_name and 'traveller' in vehicle_type_name:
                    self.vehicle_type = '17_seater_luxury_force_traveller'
                    self.passenger_capacity = 17
                elif '26' in vehicle_type_name and 'traveller' in vehicle_type_name:
                    self.vehicle_type = '26_seater_luxury_force_traveller'
                    self.passenger_capacity = 26
                elif '33' in vehicle_type_name and 'coach' in vehicle_type_name:
                    self.vehicle_type = '33_seater_super_luxury_recliner_ac_coach'
                    self.passenger_capacity = 33
                elif '41' in vehicle_type_name and 'coach' in vehicle_type_name:
                    self.vehicle_type = '41_seater_super_luxury_recliner_ac_coach'
                    self.passenger_capacity = 41
                elif '48' in vehicle_type_name and 'coach' in vehicle_type_name:
                    self.vehicle_type = '48_seater_luxury_ac_coach'
                    self.passenger_capacity = 48
                elif '49' in vehicle_type_name and 'coach' in vehicle_type_name:
                    self.vehicle_type = '49_seater_super_luxury_ac_coach_2024'
                    self.passenger_capacity = 49
                elif '50' in vehicle_type_name and 'coach' in vehicle_type_name:
                    self.vehicle_type = '50_seater_super_luxury_ac_coach_2025'
                    self.passenger_capacity = 50
                elif 'innova' in vehicle_type_name:
                    if 'crysta' in vehicle_type_name:
                        self.vehicle_type = 'toyota_innova_crysta'
                    else:
                        self.vehicle_type = 'toyota_innova'
                    self.passenger_capacity = 7
                elif 'ertiga' in vehicle_type_name:
                    self.vehicle_type = 'ertiga'
                    self.passenger_capacity = 7
                elif 'amaze' in vehicle_type_name:
                    self.vehicle_type = 'honda_amaze'
                    self.passenger_capacity = 5
                elif 'aura' in vehicle_type_name:
                    self.vehicle_type = 'hyundai_aura'
                    self.passenger_capacity = 5
                elif 'xcent' in vehicle_type_name:
                    self.vehicle_type = 'hyundai_xcent'
                    self.passenger_capacity = 5
                elif 'tavera' in vehicle_type_name:
                    self.vehicle_type = 'tavera'
                    self.passenger_capacity = 8
                # Fallback to more generic types
                elif 'bus' in vehicle_type_name:
                    if 'mini' in vehicle_type_name:
                        self.vehicle_type = 'mini_bus'
                        self.passenger_capacity = 15
                    else:
                        self.vehicle_type = 'bus'
                        self.passenger_capacity = 40
                elif 'sedan' in vehicle_type_name:
                    self.vehicle_type = 'sedan'
                    self.passenger_capacity = 4
                elif 'suv' in vehicle_type_name:
                    self.vehicle_type = 'suv'
                    self.passenger_capacity = 7
                elif 'coach' in vehicle_type_name:
                    self.vehicle_type = '26_seater_ac_coach'
                    self.passenger_capacity = 26
                
            # Map maintenance fields
            self.current_odometer = self.simply_fleet_vehicle_id.initial_odometer or 0.0
            
            # Update status if possible
            simply_state = self.simply_fleet_vehicle_id.state
            if simply_state == 'active':
                self.state = 'available'
            elif simply_state == 'maintenance':
                self.state = 'maintenance'
            elif simply_state == 'inactive':
                self.state = 'out_of_service'
                
    # Action to view the original Simply Fleet vehicle
    def action_view_simply_fleet_vehicle(self):
        self.ensure_one()
        if not self.simply_fleet_vehicle_id:
            return
            
        return {
            'name': _('Simply Fleet Vehicle'),
            'type': 'ir.actions.act_window',
            'res_model': 'simply.fleet.vehicle',
            'view_mode': 'form',
            'res_id': self.simply_fleet_vehicle_id.id,
        }