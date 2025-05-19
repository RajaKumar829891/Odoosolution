/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";

class GoogleMapWidget extends Component {
    static template = 'fleet_booking.GoogleMapWidget';
    static props = {
        record: { type: Object },
        fields: { type: Array },
        apiKeyField: { type: String },
        polylineField: { type: String, optional: true },
        markerTitleField: { type: String, optional: true },
    };

    setup() {
        this.mapRef = useRef("map");
        this.orm = useService("orm");
        this.map = null;
        this.markers = [];
        this.directionsService = null;
        this.directionsRenderer = null;
        
        // Initialize the map when component is mounted
        onMounted(() => this.initializeMap());
        
        // Clean up when component is unmounted
        onWillUnmount(() => this.destroyMap());
    }
    
    async initializeMap() {
        try {
            // Get API key from system parameters
            const apiKey = await this.getGoogleMapsApiKey();
            
            // Load Google Maps API script if not already loaded
            await this.loadGoogleMapsScript(apiKey);
            
            // Initialize map
            const mapOptions = {
                center: { lat: 0, lng: 0 },
                zoom: 2,
                mapTypeId: google.maps.MapTypeId.ROADMAP
            };
            
            this.map = new google.maps.Map(this.mapRef.el, mapOptions);
            this.directionsService = new google.maps.DirectionsService();
            this.directionsRenderer = new google.maps.DirectionsRenderer({
                map: this.map,
                suppressMarkers: false
            });
            
            // Draw the route
            this.drawRoute();
            
        } catch (error) {
            console.error("Error initializing Google Maps:", error);
        }
    }
    
    async getGoogleMapsApiKey() {
        // Fetch the API key from system parameters
        try {
            const apiKeyParam = this.props.apiKeyField || 'fleet_booking.google_maps_api_key';
            const result = await this.orm.call(
                'ir.config_parameter', 
                'get_param', 
                [apiKeyParam]
            );
            return result || '';
        } catch (error) {
            console.error("Error fetching Google Maps API key:", error);
            return '';
        }
    }
    
    loadGoogleMapsScript(apiKey) {
        return new Promise((resolve, reject) => {
            // If Google Maps API is already loaded, resolve immediately
            if (window.google && window.google.maps) {
                resolve();
                return;
            }
            
            // Create script element
            const script = document.createElement('script');
            script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places,geometry&callback=initGoogleMapCallback`;
            script.async = true;
            script.defer = true;
            
            // Define callback function
            window.initGoogleMapCallback = () => {
                resolve();
            };
            
            // Handle errors
            script.onerror = () => {
                reject(new Error('Failed to load Google Maps API'));
            };
            
            // Append script to document
            document.head.appendChild(script);
        });
    }
    
    drawRoute() {
        if (!this.map || !this.props.record.data) {
            return;
        }
        
        const record = this.props.record.data;
        
        // Clear existing markers
        this.clearMarkers();
        
        // Check if we have polyline data
        if (this.props.polylineField && record[this.props.polylineField]) {
            this.drawPolyline(record[this.props.polylineField]);
            return;
        }
        
        // Otherwise use the coordinates to create a route
        const startLat = record.start_latitude;
        const startLng = record.start_longitude;
        const endLat = record.end_latitude;
        const endLng = record.end_longitude;
        
        if (startLat && startLng && endLat && endLng) {
            const startLocation = new google.maps.LatLng(startLat, startLng);
            const endLocation = new google.maps.LatLng(endLat, endLng);
            
            // Add markers for start and end
            this.addMarker(startLocation, 'Start: ' + record.start_location);
            this.addMarker(endLocation, 'End: ' + record.end_location);
            
            // Fit bounds to include all markers
            this.fitMapToMarkers();
            
            // If we have start and end locations, calculate the route
            if (record.start_location && record.end_location) {
                this.calculateRoute(record.start_location, record.end_location);
            }
        }
    }
    
    drawPolyline(polyline) {
        if (!polyline || !this.map) {
            return;
        }
        
        // Decode the polyline
        const path = google.maps.geometry.encoding.decodePath(polyline);
        
        // Create a new polyline
        const routePath = new google.maps.Polyline({
            path: path,
            geodesic: true,
            strokeColor: '#FF0000',
            strokeOpacity: 1.0,
            strokeWeight: 3
        });
        
        // Add the polyline to the map
        routePath.setMap(this.map);
        
        // Add markers for start and end
        if (path.length > 0) {
            this.addMarker(path[0], 'Start');
            this.addMarker(path[path.length - 1], 'End');
            
            // Fit map to polyline bounds
            const bounds = new google.maps.LatLngBounds();
            path.forEach(location => bounds.extend(location));
            this.map.fitBounds(bounds);
        }
    }
    
    calculateRoute(origin, destination) {
        if (!this.directionsService || !this.directionsRenderer) {
            return;
        }
        
        // Get via points
        const viaStops = this.props.record.data.via_stops;
        let waypoints = [];
        
        if (viaStops) {
            waypoints = viaStops.split('\n').map(stop => ({
                location: stop.trim(),
                stopover: true
            }));
        }
        
        // Calculate route
        this.directionsService.route({
            origin: origin,
            destination: destination,
            waypoints: waypoints,
            travelMode: google.maps.TravelMode.DRIVING,
            optimizeWaypoints: true
        }, (response, status) => {
            if (status === 'OK') {
                this.directionsRenderer.setDirections(response);
            } else {
                console.error('Directions request failed due to ' + status);
            }
        });
    }
    
    addMarker(location, title) {
        const marker = new google.maps.Marker({
            position: location,
            map: this.map,
            title: title
        });
        
        this.markers.push(marker);
    }
    
    clearMarkers() {
        this.markers.forEach(marker => marker.setMap(null));
        this.markers = [];
    }
    
    fitMapToMarkers() {
        if (this.markers.length === 0) {
            return;
        }
        
        const bounds = new google.maps.LatLngBounds();
        this.markers.forEach(marker => bounds.extend(marker.getPosition()));
        this.map.fitBounds(bounds);
    }
    
    destroyMap() {
        // Clean up resources
        this.clearMarkers();
        this.map = null;
        this.directionsService = null;
        this.directionsRenderer = null;
    }
}

// Register the widget with the web components registry
registry.category("view_widgets").add("google_map", GoogleMapWidget);

export default GoogleMapWidget;