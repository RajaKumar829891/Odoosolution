/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";

export class GoogleMapsRouteWidget extends Component {
    static template = "fleet_booking.GoogleMapsRouteWidgetTemplate";
    static props = {
        ...standardFieldProps,
        start_location: { type: String, optional: true },
        end_location: { type: String, optional: true },
        via_stops: { type: String, optional: true },
    };

    setup() {
        this.mapRef = useRef("map");
        this.startInputRef = useRef("startInput");
        this.endInputRef = useRef("endInput");
        this.viaStopsRef = useRef("viaStops");
        
        this.state = useState({
            distance: 0,
            duration: 0,
            isLoading: false,
            mapUrl: null,
        });

        this.directionsService = null;
        this.directionsRenderer = null;
        this.map = null;
        this.geocoder = null;

        onMounted(() => {
            this.initializeMap();
        });

        onWillUnmount(() => {
            if (this.directionsRenderer) {
                this.directionsRenderer.setMap(null);
            }
        });
    }

    async initializeMap() {
        if (typeof google === 'undefined') return;

        // Initialize map centered on India
        const mapOptions = {
            center: { lat: 20.5937, lng: 78.9629 },
            zoom: 5,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
        };

        this.map = new google.maps.Map(this.mapRef.el, mapOptions);
        this.directionsService = new google.maps.DirectionsService();
        this.directionsRenderer = new google.maps.DirectionsRenderer();
        this.geocoder = new google.maps.Geocoder();
        
        this.directionsRenderer.setMap(this.map);

        // Set up autocomplete for input fields
        this.setupAutocomplete();

        // If initial values exist, calculate route
        if (this.props.record.data.journey_start_location && this.props.record.data.journey_end_location) {
            this.calculateRoute();
        }
    }

    setupAutocomplete() {
        const options = {
            componentRestrictions: { country: 'in' },
            fields: ['address_components', 'geometry', 'formatted_address'],
        };

        if (this.startInputRef.el) {
            const startAutocomplete = new google.maps.places.Autocomplete(this.startInputRef.el, options);
            startAutocomplete.addListener('place_changed', () => {
                const place = startAutocomplete.getPlace();
                this.updateField('journey_start_location', place.formatted_address);
                this.calculateRoute();
            });
        }

        if (this.endInputRef.el) {
            const endAutocomplete = new google.maps.places.Autocomplete(this.endInputRef.el, options);
            endAutocomplete.addListener('place_changed', () => {
                const place = endAutocomplete.getPlace();
                this.updateField('journey_end_location', place.formatted_address);
                this.calculateRoute();
            });
        }
    }

    async calculateRoute() {
        const start = this.props.record.data.journey_start_location;
        const end = this.props.record.data.journey_end_location;
        const viaStops = this.props.record.data.via_stops;

        if (!start || !end || !this.directionsService) return;

        this.state.isLoading = true;

        // Parse via stops
        const waypoints = [];
        if (viaStops) {
            const stops = viaStops.split('\n').filter(stop => stop.trim());
            for (const stop of stops) {
                waypoints.push({
                    location: stop,
                    stopover: true,
                });
            }
        }

        const request = {
            origin: start,
            destination: end,
            waypoints: waypoints,
            travelMode: google.maps.TravelMode.DRIVING,
            unitSystem: google.maps.UnitSystem.METRIC,
        };

        try {
            const response = await this.directionsService.route(request);
            this.directionsRenderer.setDirections(response);

            // Calculate total distance and duration
            let totalDistance = 0;
            let totalDuration = 0;

            response.routes[0].legs.forEach(leg => {
                totalDistance += leg.distance.value;
                totalDuration += leg.duration.value;
            });

            // Update fields
            this.updateField('journey_distance', totalDistance / 1000); // Convert to km
            this.updateField('journey_duration', Math.round(totalDuration / 60)); // Convert to minutes

            // Generate static map URL for display
            this.generateStaticMapUrl(response.routes[0]);

        } catch (error) {
            console.error('Error calculating route:', error);
        } finally {
            this.state.isLoading = false;
        }
    }

    generateStaticMapUrl(route) {
        const path = google.maps.geometry.encoding.encodePath(route.overview_path);
        const apiKey = 'YOUR_API_KEY'; // This should come from your configuration
        
        let url = `https://maps.googleapis.com/maps/api/staticmap?size=600x400&path=enc:${path}`;
        url += `&markers=color:green|label:A|${route.legs[0].start_location.lat()},${route.legs[0].start_location.lng()}`;
        url += `&markers=color:red|label:B|${route.legs[route.legs.length - 1].end_location.lat()},${route.legs[route.legs.length - 1].end_location.lng()}`;
        
        // Add waypoint markers
        if (route.legs.length > 1) {
            for (let i = 1; i < route.legs.length; i++) {
                url += `&markers=color:blue|label:${i}|${route.legs[i].start_location.lat()},${route.legs[i].start_location.lng()}`;
            }
        }
        
        url += `&key=${apiKey}`;
        this.state.mapUrl = url;
        
        // Update a field to store the route image URL
        this.updateField('route_map_url', url);
    }

    updateField(fieldName, value) {
        if (this.props.record.data[fieldName] !== value) {
            this.props.record.update({ [fieldName]: value });
        }
    }

    addDestination() {
        const viaStops = this.props.record.data.via_stops || '';
        const newStop = prompt('Enter destination address:');
        if (newStop) {
            const updatedStops = viaStops ? `${viaStops}\n${newStop}` : newStop;
            this.updateField('via_stops', updatedStops);
            this.calculateRoute();
        }
    }

    clearRoute() {
        if (this.directionsRenderer) {
            this.directionsRenderer.setDirections({ routes: [] });
        }
        this.updateField('journey_distance', 0);
        this.updateField('journey_duration', 0);
        this.updateField('route_map_url', '');
        this.state.mapUrl = null;
    }
}

GoogleMapsRouteWidget.template = 'fleet_booking.GoogleMapsRouteWidget';

registry.category("fields").add("google_maps_route", {
    component: GoogleMapsRouteWidget,
});