/** @odoo-module **/
import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

const { setTimeout } = browser;

// Store the original setup function
const originalSetup = KanbanController.prototype.setup;

// Patch KanbanController to add Diesel Tanker button for Fuel Log kanban view
patch(KanbanController.prototype, {
    setup() {
        // Call the original setup
        originalSetup.call(this, ...arguments);
        
        // Only add the button for Fuel Log model
        if (this.props.resModel === 'simply.fleet.fuel.log') {
            this.actionService = useService("action");
            this.orm = useService("orm");
            this._addDieselTankerButton();
        }
    },

    /**
     * Add diesel tanker button to the kanban control panel
     */
    _addDieselTankerButton() {
        setTimeout(() => {
            // Load diesel tanker data
            this._loadDieselTankerData().then(tankerData => {
                // Find the control panel
                const controlPanel = document.querySelector('.o_control_panel');
                if (!controlPanel) return;

                // Check if button already exists
                if (document.getElementById('diesel_tanker_kanban_button')) return;

                // Create button container
                const buttonContainer = document.createElement('div');
                buttonContainer.id = 'diesel_tanker_kanban_button';
                buttonContainer.className = 'btn-group ms-2';
                
                // Create button
                const buttonEl = document.createElement('button');
                buttonEl.className = 'btn btn-primary';
                buttonEl.style.display = 'flex';
                buttonEl.style.alignItems = 'center';
                buttonEl.style.gap = '0px';
                
                // Set click handler
                buttonEl.addEventListener('click', () => {
                    this.actionService.doAction({
                        type: 'ir.actions.act_window',
                        name: 'Diesel Tanker',
                        res_model: 'simply.fleet.diesel.tanker',
                        views: [[false, 'kanban'], [false, 'tree'], [false, 'form']],
                        target: 'current',
                    });
                });
                
                // Set button content
                if (tankerData) {
                    // Get state-based CSS class instead of color code
                    const colorClass = tankerData.state === 'full' ? 'bg-success' : 
                                      tankerData.state === 'medium' ? 'bg-warning' : 'bg-danger';
                    
                    buttonEl.innerHTML = `
                        <div style="background-color: black; padding: 4px; border-radius: 3px; width: 160px; position: relative;">
                            <div class="d-flex align-items-start p-0 m-0" style="margin-top: -2px;">
                                <span class="me-1" style="font-size: 26px; color: red;">⛽</span>
                                <div style="flex: 1; margin-top: 3px;">
                                    <div style="width: 100%; height: 12px; position: relative; color: white; border: 1px solid white; border-radius: 2px;">
                                        <div class="o_progress align-middle overflow-hidden position-relative" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${tankerData.fuel_percentage}" style="width: 100%; height: 10px;">
                                            <div class="${colorClass} h-100" style="width: ${tankerData.fuel_percentage}%"></div>
                                            <span style="color: white; font-size: 11px; position: absolute; right: 3px; top: 50%; transform: translateY(-50%);">${Math.round(tankerData.fuel_percentage)}%</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div style="color: #aaa; font-size: 12px; font-weight: bold; text-align: right; position: absolute; bottom: 4px; right: 4px; width: calc(100% - 8px);">
                                AVL.Fuel: ${tankerData.current_fuel_level.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})} L
                            </div>
                        </div>
                    `;
                } else {
                    buttonEl.innerHTML = `<span>Diesel Tanker</span>`;
                }
                
                // Add button to container
                buttonContainer.appendChild(buttonEl);
                
                // Insert button in control panel
                const searchBar = controlPanel.querySelector('.o_searchview');
                if (searchBar && searchBar.parentNode) {
                    searchBar.parentNode.insertBefore(buttonContainer, searchBar);
                } else {
                    // Fallback insertion point
                    const viewSwitcher = controlPanel.querySelector('.o_cp_switch_buttons');
                    if (viewSwitcher && viewSwitcher.parentNode) {
                        viewSwitcher.parentNode.insertBefore(buttonContainer, viewSwitcher);
                    }
                }
            });
        }, 300);
    },
    
    /**
     * Load diesel tanker data from the server
     */
    async _loadDieselTankerData() {
        try {
            // Get the tanker with highest fuel level
            const tankers = await this.orm.searchRead(
                'simply.fleet.diesel.tanker',
                [['active', '=', true]],
                ['name', 'current_fuel_level', 'capacity', 'fuel_percentage', 'state'],
                { limit: 1, order: 'current_fuel_level DESC' }
            );
            
            if (tankers && tankers.length > 0) {
                return tankers[0];
            }
            return null;
        } catch (error) {
            console.error("Failed to load tanker data:", error);
            return null;
        }
    }
});