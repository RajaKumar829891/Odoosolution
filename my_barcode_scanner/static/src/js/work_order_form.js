/** @odoo-module **/
import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { useService } from "@web/core/utils/hooks";

class WorkOrderFormController extends formView.Controller {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        // Process URL parameters on form load
        this._processUrlParams();
    }
    
    _processUrlParams() {
        const urlParams = new URLSearchParams(window.location.search);
        const barcode = urlParams.get('barcode');
        
        if (barcode && this.model.root.resId) {
            // Process the barcode
            this._processBarcode(barcode);
            
            // Clean up URL by removing the barcode parameter
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.delete('barcode');
            window.history.replaceState({}, '', newUrl);
        }
    }
    
    async _processBarcode(barcode) {
        try {
            const result = await this.orm.call(
                'simply.vehicle.work.order',
                'add_product_from_barcode',
                [this.model.root.resId, barcode]
            );
            
            if (result.success) {
                this.notification.add(`Added ${result.product_name} to order`, { type: "success" });
                // Reload the form to show the new line
                await this.model.root.load();
                await this.model.root.save();
            } else {
                this.notification.add(result.message || "Error processing barcode", { type: "danger" });
            }
        } catch (error) {
            this.notification.add("Server error: " + error, { type: "danger" });
        }
    }
}

// Register the custom form controller for work orders
registry.category("views").add("simply_vehicle_work_order_form", {
    ...formView,
    Controller: WorkOrderFormController,
});
