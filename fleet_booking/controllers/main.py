from odoo import http
from odoo.http import request
import json


class FleetBookingController(http.Controller):
    
    @http.route('/fleet_booking/get_vehicle_info/<int:vehicle_id>', type='json', auth='user')
    def get_vehicle_info(self, vehicle_id, **kwargs):
        vehicle = request.env['fleet.vehicle'].browse(vehicle_id)
        if not vehicle.exists():
            return {'error': 'Vehicle not found'}
        
        return {
            'id': vehicle.id,
            'name': vehicle.name,
            'vehicle_type': vehicle.vehicle_type,
            'passenger_capacity': vehicle.passenger_capacity,
            'luggage_capacity': vehicle.luggage_capacity,
            'base_rental_price': vehicle.base_rental_price,
            'cost_per_km': vehicle.cost_per_km,
            'state': vehicle.state,
            'has_ac': vehicle.has_ac,
            'has_wifi': vehicle.has_wifi,
            'has_usb_charging': vehicle.has_usb_charging,
        }
    
    @http.route('/fleet_booking/calculate_journey_price', type='json', auth='user')
    def calculate_journey_price(self, **kwargs):
        distance = float(kwargs.get('distance', 0))
        vehicle_type = kwargs.get('vehicle_type')
        start_date = kwargs.get('start_date')
        
        # Simple pricing calculation
        base_price = 0
        price_per_km = 0
        
        if vehicle_type == '26_seater_ac_coach':
            base_price = 5000
            price_per_km = 50
        elif vehicle_type == 'sedan':
            base_price = 1000
            price_per_km = 15
        elif vehicle_type == 'suv':
            base_price = 1500
            price_per_km = 20
        elif vehicle_type == 'mini_bus':
            base_price = 3000
            price_per_km = 30
        elif vehicle_type == 'bus':
            base_price = 6000
            price_per_km = 60
        
        total_price = base_price + (distance * price_per_km)
        
        # Apply weekend or holiday surcharge if applicable
        # This would use the start_date to check for weekends/holidays
        
        return {
            'base_price': base_price,
            'distance_charge': distance * price_per_km,
            'total_price': total_price,
            'currency': request.env.company.currency_id.symbol
        }
    
    @http.route('/fleet_booking/check_driver_availability', type='json', auth='user')
    def check_driver_availability(self, start_date, end_date, **kwargs):
        # Find available drivers for the given date range
        domain = [
            ('state', '=', 'available'),
            ('active', '=', True)
        ]
        
        available_drivers = request.env['fleet.driver'].search_read(
            domain=domain,
            fields=['id', 'name', 'mobile', 'license_type', 'rating'],
            limit=10
        )
        
        return {
            'available_drivers': available_drivers,
            'count': len(available_drivers)
        }
    
    @http.route('/fleet_booking/get_journey_stats', type='http', auth='user')
    def get_journey_stats(self, **kwargs):
        # Simple stats for journeys/bookings
        completed_bookings = request.env['fleet.booking'].search_count([
            ('state', '=', 'completed')
        ])
        
        confirmed_bookings = request.env['fleet.booking'].search_count([
            ('state', '=', 'confirmed')
        ])
        
        all_bookings = request.env['fleet.booking'].search_count([])
        
        data = {
            'completed': completed_bookings,
            'confirmed': confirmed_bookings,
            'total': all_bookings,
            'upcoming': confirmed_bookings,
            'completion_rate': (completed_bookings / all_bookings * 100) if all_bookings else 0
        }
        
        return json.dumps(data)