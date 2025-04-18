/** @odoo-module **/
import { browser } from "@web/core/browser/browser";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

const { setTimeout } = browser;

// Store the original setup function to call it later
const originalSetup = ListController.prototype.setup;

patch(ListController.prototype, {
    setup() {
        // Call the original setup
        originalSetup.call(this, ...arguments);
        
        // Only proceed if we're in the fuel logs view
        if (this.props.resModel === 'simply.fleet.fuel.log') {
            this.actionService = useService("action");
            this.orm = useService("orm");
            this.loadTankerData();
        }
    },

    async loadTankerData() {
        try {
            // Get the tanker with highest fuel level
            const tankers = await this.orm.searchRead(
                'simply.fleet.diesel.tanker',
                [['active', '=', true]],
                ['name', 'current_fuel_level', 'capacity', 'fuel_percentage', 'state'],
                { limit: 1, order: 'current_fuel_level DESC' }
            );
            
            if (tankers && tankers.length > 0) {
                this.tankerData = tankers[0];
                this.updateTankerButton();
            }
        } catch (error) {
            console.error("Failed to load tanker data:", error);
        }
    },

    updateTankerButton() {
        if (!this.tankerData) return;
        
        // Wait for the DOM to be ready
        setTimeout(() => {
            const breadcrumbs = document.querySelector('.o_control_panel_breadcrumbs');
            if (!breadcrumbs) return;
            
            // Check if button already exists
            if (document.getElementById('diesel_tanker_progress_button')) return;
            
            // Get state-based color
            const colorClass = this.tankerData.state === 'full' ? 'bg-success' : 
                              this.tankerData.state === 'medium' ? 'bg-warning' : 'bg-danger';
            
            // Create button with progress bar
            const buttonEl = document.createElement('div');
            buttonEl.id = 'diesel_tanker_progress_button';
            buttonEl.className = 'o_cell o_wrap_input flex-grow-1 flex-sm-grow-0 text-break ms-3';
            buttonEl.style.width = '300px';
            buttonEl.style.cursor = 'pointer';
            
            // Add click handler
            buttonEl.addEventListener('click', () => {
                this.actionService.doAction({
                    type: 'ir.actions.act_window',
                    name: 'Diesel Tanker',
                    res_model: 'simply.fleet.diesel.tanker',
                    views: [[false, 'kanban'], [false, 'tree'], [false, 'form']],
                    target: 'current',
                });
            });
            
            buttonEl.innerHTML = `
            <div style="background-color: black; padding: 4px; border-radius: 3px; width: 160px; position: relative;">
                <div class="d-flex align-items-start p-0 m-0" style="margin-top: -2px;">
                    <span class="me-1" style="font-size: 26px; color: red;">⛽</span>
                    <div style="flex: 1; margin-top: 3px;">
                        <div style="width: 100%; height: 12px; position: relative; color: white; border: 1px solid white; border-radius: 2px;">
                            <div class="o_progress align-middle overflow-hidden position-relative" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${this.tankerData.fuel_percentage}" style="width: 100%; height: 10px;">
                                <div class="${colorClass} h-100" style="width: ${this.tankerData.fuel_percentage}%"></div>
                                <span style="color: white; font-size: 11px; position: absolute; right: 3px; top: 50%; transform: translateY(-50%);">${Math.round(this.tankerData.fuel_percentage)}%</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div style="color: #aaa; font-size: 12px; font-weight: bold; text-align: right; position: absolute; bottom: 4px; right: 4px; width: calc(100% - 8px);">
                    AVL.Fuel: ${this.tankerData.current_fuel_level.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})} L
                </div>
            </div>
        `;
            
            // Insert after Fuel Logs text
            const fuelLogsText = Array.from(breadcrumbs.querySelectorAll('.o_breadcrumb_item'))
                .find(el => el.textContent.includes('Fuel Logs'));
                
            if (fuelLogsText) {
                fuelLogsText.parentNode.insertBefore(buttonEl, fuelLogsText.nextSibling);
            } else {
                breadcrumbs.appendChild(buttonEl);
            }
            
        }, 500); // Give some time for DOM to be ready
    }
});

// Store the original onMounted function to call it later
const originalOnMounted = ListController.prototype.onMounted;

// Patch the onMounted method only if it exists
if (originalOnMounted) {
    patch(ListController.prototype, {
        onMounted() {
            // Call the original onMounted
            originalOnMounted.call(this, ...arguments);
            
            if (this.props.resModel === 'simply.fleet.fuel.log' && this.tankerData) {
                this.updateTankerButton();
            }
        }
    });
}