/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, "bluetooth_printer_discovery_controller", {
    setup() {
        this._super(...arguments);
        this.scanPollInterval = null;
        
        // When the component is mounted, check if it's our target model
        this.env.bus.addEventListener("MOUNTED", () => {
            if (this.model.root.resModel === "bluetooth.printer.discovery") {
                this._setupPolling();
            }
        });
        
        // Clean up when component is destroyed
        this.env.bus.addEventListener("WILL_UNMOUNT", () => {
            if (this.scanPollInterval) {
                clearInterval(this.scanPollInterval);
                this.scanPollInterval = null;
            }
        });
    },
    
    /**
     * Setup polling for printer scan results
     */
    _setupPolling() {
        if (this.scanPollInterval) {
            clearInterval(this.scanPollInterval);
        }
        
        let pollCount = 0;
        const maxPolls = 15; // Maximum 15 seconds
        
        this.scanPollInterval = setInterval(async () => {
            pollCount++;
            
            try {
                // Get the active record
                const recordId = this.model.root.resId;
                
                // Call the method to check for results
                const foundResults = await this.orm.call(
                    "bluetooth.printer.discovery",
                    "_poll_scan_results",
                    [recordId]
                );
                
                if (foundResults) {
                    // We found results, stop polling and reload
                    clearInterval(this.scanPollInterval);
                    this.scanPollInterval = null;
                    await this.model.root.load();
                    this.render(true);
                } else if (pollCount >= maxPolls) {
                    // Stop polling after max attempts
                    clearInterval(this.scanPollInterval);
                    this.scanPollInterval = null;
                    
                    // Update the message
                    await this.orm.write("bluetooth.printer.discovery", [recordId], {
                        scan_message: "Scan timeout. No printers found or error occurred. Try scanning again."
                    });
                    
                    await this.model.root.load();
                    this.render(true);
                }
            } catch (error) {
                console.error("Error polling for printer scan results:", error);
                clearInterval(this.scanPollInterval);
                this.scanPollInterval = null;
            }
        }, 1000);
    },
});
