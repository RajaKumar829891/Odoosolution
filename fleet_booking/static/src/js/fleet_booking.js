/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { FormRenderer } from "@web/views/form/form_renderer";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";
import { Component, onWillStart, useState, onMounted } from "@odoo/owl";

// Patch the FormRenderer to add functionality for journey price calculation
const OriginalFormRendererSetup = FormRenderer.prototype.setup;
patch(FormRenderer.prototype, {
    setup() {
        OriginalFormRendererSetup.call(this, ...arguments);
        this.orm = useService("orm");
    },

    /**
     * Calculate journey price based on distance and vehicle type
     * @private
     * @param {Float} distance
     * @param {String} vehicleType
     */
    async calculateJourneyPrice(distance, vehicleType) {
        if (!distance || !vehicleType) {
            return;
        }
        
        try {
            const price = await this.orm.call(
                'fleet.booking',
                'calculate_journey_price',
                [],
                {
                    distance: distance,
                    vehicle_type: vehicleType
                }
            );
            
            if (price) {
                // Update the model
                this.props.record.update({
                    journey_price: price.base_price + price.distance_charge,
                    vat_amount: (price.base_price + price.distance_charge) * 0.18, // Assuming 18% VAT
                });
            }
        } catch (error) {
            console.error("Error calculating journey price:", error);
        }
    }
});

// Patch the FormController to add event handlers
const OriginalFormControllerSetup = FormController.prototype.setup;
patch(FormController.prototype, {
    setup() {
        OriginalFormControllerSetup.call(this, ...arguments);
        
        // Add event listeners for the journey distance and vehicle type changes
        this.env.bus.addEventListener('journey_distance_changed', this._onJourneyDistanceChange.bind(this));
        this.env.bus.addEventListener('vehicle_type_changed', this._onVehicleTypeChange.bind(this));
    },

    /**
     * When the journey distance changes, recalculate price if vehicle type is set
     * @private
     * @param {Event} ev
     */
    _onJourneyDistanceChange(ev) {
        const { distance } = ev.detail;
        const vehicleType = this.model.root.data.vehicle_type_id && this.model.root.data.vehicle_type_id[0];
        
        if (vehicleType) {
            this.renderer.calculateJourneyPrice(distance, vehicleType);
        }
    },

    /**
     * When the vehicle type changes, recalculate price if distance is set
     * @private
     * @param {Event} ev
     */
    _onVehicleTypeChange(ev) {
        const { vehicleTypeId } = ev.detail;
        const distance = this.model.root.data.journey_distance;
        
        if (distance) {
            this.renderer.calculateJourneyPrice(distance, vehicleTypeId);
        }
    }
});

// Patch the Many2OneField to add functionality for driver availability check
const OriginalMany2OneFieldSetup = Many2OneField.prototype.setup;
patch(Many2OneField.prototype, {
    setup() {
        OriginalMany2OneFieldSetup.call(this, ...arguments);
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        // Only apply for driver_id field in fleet.booking model
        this.isDriverField = this.props.record && 
                            this.props.record.resModel === 'fleet.booking' && 
                            this.props.name === 'driver_id';
    },

    /**
     * Check driver availability based on booking dates
     */
    async checkDriverAvailability() {
        if (!this.isDriverField) {
            return;
        }
        
        const journeyStartDate = this.props.record.data.journey_start_date;
        
        if (!journeyStartDate) {
            this.notification.add(
                'Please set a journey date first.',
                { type: 'warning', title: 'Missing Information' }
            );
            return;
        }
        
        try {
            const drivers = await this.orm.call(
                'fleet.booking',
                'check_driver_availability',
                [],
                { start_date: journeyStartDate }
            );
            
            if (drivers && drivers.available_drivers) {
                this.notification.add(
                    `Available Drivers: ${drivers.count}`,
                    { type: 'success', title: 'Driver Availability' }
                );
            } else {
                this.notification.add(
                    'No available drivers found for the selected date.',
                    { type: 'warning', title: 'No Drivers' }
                );
            }
        } catch (error) {
            console.error("Error checking driver availability:", error);
            this.notification.add(
                'Error checking driver availability.',
                { type: 'danger', title: 'Error' }
            );
        }
    }
});

// Create a new Dashboard component with Owl
class FleetBookingDashboard extends Component {
    static template = 'fleet_booking.Dashboard';
    
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            dashboardData: {},
            loading: true
        });
        
        onWillStart(async () => {
            await this.fetchDashboardData();
        });
    }
    
    /**
     * Fetch dashboard data from the server
     */
    async fetchDashboardData() {
        try {
            this.state.loading = true;
            const data = await this.orm.call(
                'fleet.booking',
                'get_journey_stats',
                []
            );
            this.state.dashboardData = typeof data === 'string' ? JSON.parse(data) : data;
        } catch (error) {
            console.error("Error fetching dashboard data:", error);
        } finally {
            this.state.loading = false;
        }
    }
    
    /**
     * Handle click on dashboard widgets
     * @param {Event} ev
     */
    onWidgetClick(ev) {
        const actionName = ev.currentTarget.dataset.action;
        if (actionName) {
            this.action.doAction(actionName);
        }
    }
}

// Register the FleetBookingDashboard component with the action registry
registry.category("actions").add("fleet_booking_dashboard", FleetBookingDashboard);

// Define field components to handle events
export class FleetDistanceField extends Component {
    static template = 'fleet_booking.DistanceField';
    static props = {
        record: { type: Object },
        name: { type: String }
    };
    
    setup() {
        this.env = useService("env");
    }
    
    /**
     * When the journey distance changes, trigger an event
     * @param {Event} ev
     */
    onDistanceChange(ev) {
        const distanceValue = parseFloat(ev.target.value || 0);
        this.env.bus.trigger('journey_distance_changed', { distance: distanceValue });
    }
}

export class FleetVehicleTypeField extends Component {
    static template = 'fleet_booking.VehicleTypeField';
    static props = {
        record: { type: Object },
        name: { type: String }
    };
    
    setup() {
        this.env = useService("env");
    }
    
    /**
     * When the vehicle type changes, trigger an event
     * @param {Event} ev
     */
    onVehicleTypeChange(ev) {
        const vehicleTypeId = ev.target.value;
        this.env.bus.trigger('vehicle_type_changed', { vehicleTypeId });
    }
}

export class DriverSelectField extends Component {
    static template = 'fleet_booking.DriverSelectField';
    static props = {
        record: { type: Object },
        name: { type: String }
    };
    
    setup() {
        this.many2OneField = useService("many2one_field");
    }
    
    /**
     * Check driver availability
     */
    checkAvailability() {
        this.many2OneField.checkDriverAvailability();
    }
}

// Register the custom field components
registry.category("fields").add("fleet_distance", FleetDistanceField);
registry.category("fields").add("fleet_vehicle_type", FleetVehicleTypeField);
registry.category("fields").add("fleet_driver_select", DriverSelectField);