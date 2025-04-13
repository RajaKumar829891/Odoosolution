/** @odoo-module **/
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class BarcodeHandlerNextline extends Component {
    static template = 'my_barcode_scanner.BarcodeHandlerNextline';
    static props = {
        ...standardFieldProps,
    };
    
    setup() {
        this.inputRef = useRef("input");
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        // Listen for barcode input events
        onMounted(() => {
            // Register keydown event on the input field for manual entry
            if (this.inputRef.el) {
                this.inputRef.el.addEventListener('keydown', this.handleKeyDown.bind(this));
            }
        });
        
        onWillUnmount(() => {
            // Clean up event listener
            if (this.inputRef.el) {
                this.inputRef.el.removeEventListener('keydown', this.handleKeyDown.bind(this));
            }
        });
    }
    
    onInput(ev) {
        this.props.update(ev.target.value);
    }
    
    async handleKeyDown(ev) {
        if (ev.key === 'Enter') {
            ev.preventDefault();
            
            // Process the barcode entered manually
            const barcode = ev.target.value;
            if (barcode) {
                await this.handleBarcodeScan(barcode);
                // Clear the input field after processing
                ev.target.value = "";
            }
        }
    }
    
    async handleBarcodeScan(barcode) {
        try {
            // Get the current record ID
            const recordId = this.props.record.resId;
            
            if (!recordId) {
                this.notification.add("No record selected", { type: "warning" });
                return;
            }
            
            // Call the server method to add the product
            const result = await this.orm.call(
                'simply.vehicle.work.order',
                'add_product_from_barcode',
                [recordId, barcode]
            );
            
            if (result.success) {
                this.notification.add(`Added ${result.product_name} to order`, { type: "success" });
                
                // Refresh the view to show the new line
                await this.props.record.model.load();
                this.props.record.model.notify();
            } else {
                this.notification.add(result.message || "Error processing barcode", { type: "danger" });
            }
        } catch (error) {
            this.notification.add("Server error: " + error, { type: "danger" });
        }
    }
}

registry.category("fields").add("barcode_handler_nextline", BarcodeHandlerNextline);
