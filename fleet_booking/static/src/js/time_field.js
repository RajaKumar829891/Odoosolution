/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useInputField } from "@web/views/fields/input_field_hook";
import { Component, onMounted, onWillUpdateProps, useRef } from "@odoo/owl";

export class TimeField extends Component {
    static template = "fleet_booking.TimeField";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.input = useRef("input");
        this.ampm = useRef("ampm");
        
        onMounted(() => this.initializeTime());
        onWillUpdateProps(() => this.initializeTime());
    }
    
    initializeTime() {
        if (this.props.readonly) {
            return;
        }
        
        if (this.props.value) {
            // Parse time like "08:00 AM"
            const parts = this.props.value.split(' ');
            if (parts.length === 2) {
                this.input.el.value = parts[0];
                this.ampm.el.value = parts[1];
            }
        }
    }
    
    onChange() {
        const timeValue = this.input.el.value;
        const ampmValue = this.ampm.el.value;
        
        if (timeValue) {
            const formattedValue = timeValue + ' ' + ampmValue;
            this.props.update(formattedValue);
        }
    }
}

registry.category("fields").add("time_picker", TimeField);