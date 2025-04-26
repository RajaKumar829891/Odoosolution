/** @odoo-module **/
import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";
import { ListController } from "@web/views/list/list_controller";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

const { setTimeout } = browser;

/**
 * Common function to load diesel tanker data
 * This centralizes the data fetching logic to avoid duplication
 */
async function loadDieselTankerData(orm) {
    try {
        // Get the tanker with highest fuel level
        const tankers = await orm.searchRead(
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

/**
 * Common function to create diesel tanker button HTML
 * This centralizes the button rendering logic to ensure consistency
 */
function createDieselTankerButtonHTML(tankerData) {
    if (!tankerData) return '<span>Diesel Tanker</span>';
    
    // Get state-based CSS class
    const colorClass = tankerData.state === 'full' ? 'bg-success' : 
                      tankerData.state === 'medium' ? 'bg-warning' : 'bg-danger';
    
    return `
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
}

// ----- LIST CONTROLLER PATCH -----

// Store the original setup function to call it later
const originalListSetup = ListController.prototype.setup;

patch(ListController.prototype, {
    setup() {
        // Call the original setup
        originalListSetup.call(this, ...arguments);
        
        // Only proceed if we're in the fuel logs view
        if (this.props.resModel === 'simply.fleet.fuel.log') {
            this.actionService = useService("action");
            this.orm = useService("orm");
            this.loadTankerData();
        }
    },

    async loadTankerData() {
        // Use the common data loading function
        this.tankerData = await loadDieselTankerData(this.orm);
        if (this.tankerData) {
            this.updateTankerButton();
        }
    },

    async updateTankerButton() {
    if (!this.tankerData) return;
    
    // Wait for the DOM to be ready
    setTimeout(() => {
        // Find the breadcrumbs container - UPDATED to match the div in the screenshot
        const breadcrumbsContainer = document.querySelector('.o_control_panel_breadcrumbs');
        if (!breadcrumbsContainer) return;
        
        // Check if button already exists
        const existingButton = document.getElementById('diesel_tanker_progress_button') ||
                             document.getElementById('diesel_tanker_kanban_button');
        if (existingButton) {
            existingButton.remove();
        }
        
        // Create button with progress bar
        const buttonEl = document.createElement('div');
        buttonEl.id = 'diesel_tanker_progress_button';
        buttonEl.className = 'ms-3';
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
        
        // Use the common button HTML function
        buttonEl.innerHTML = createDieselTankerButtonHTML(this.tankerData);
        
        // Insert directly into the breadcrumbs container
        breadcrumbsContainer.appendChild(buttonEl);
        
        // Set global flag to true
        dieselTankerButtonAdded = true;
        
    }, 500); // Give some time for DOM to be ready
}
});

// Store the original onMounted function to call it later
const originalListOnMounted = ListController.prototype.onMounted;

// Patch the onMounted method only if it exists
if (originalListOnMounted) {
    patch(ListController.prototype, {
        onMounted() {
            // Call the original onMounted
            originalListOnMounted.call(this, ...arguments);
            
            // Check global flag before adding button
            if (this.props.resModel === 'simply.fleet.fuel.log' && this.tankerData && !dieselTankerButtonAdded) {
                // Remove any existing button first
                const existingButton = document.getElementById('diesel_tanker_kanban_button') || 
                                     document.getElementById('diesel_tanker_progress_button');
                if (existingButton) {
                    existingButton.remove();
                }
                
                this.updateTankerButton();
                // Set global flag to true
                dieselTankerButtonAdded = true;
            }
        }
    });
}

/**
 * Global variable to track if the diesel tanker button has been added
 * This ensures we only add the button once regardless of controller type
 */
let dieselTankerButtonAdded = false;

// Function to reset the button added state when switching views
function resetDieselTankerButtonState() {
    // Add event listener for view switching
    document.addEventListener('click', (e) => {
        // If clicking on view switcher buttons
        if (e.target && (e.target.closest('.o_cp_switch_buttons') || 
                         e.target.closest('.nav-link'))) {
            // Reset the flag after a small delay to ensure view has changed
            setTimeout(() => {
                dieselTankerButtonAdded = false;
            }, 100);
        }
    });
}
// Initialize the reset functionality
resetDieselTankerButtonState();

// ----- KANBAN CONTROLLER PATCH -----

// Store the original setup function
const originalKanbanSetup = KanbanController.prototype.setup;

// Patch KanbanController to add Diesel Tanker button for Fuel Log kanban view
patch(KanbanController.prototype, {
    setup() {
        // Call the original setup
        originalKanbanSetup.call(this, ...arguments);
        
        // Only add the button for Fuel Log model
        if (this.props.resModel === 'simply.fleet.fuel.log') {
            this.actionService = useService("action");
            this.orm = useService("orm");
            
            // Add button after a small delay to ensure view is ready
            setTimeout(() => {
                this._addDieselTankerButton();
            }, 500);
        }
    },

    /**
 * Add diesel tanker button to the kanban control panel
 */
async _addDieselTankerButton() {
    // Check global flag first
    if (dieselTankerButtonAdded) {
        return;
    }
    
    // First load the tanker data
    const tankerData = await loadDieselTankerData(this.orm);
    
    // Wait for DOM to be ready
    setTimeout(() => {
        // Find the breadcrumbs container - THIS IS THE KEY CHANGE
        const breadcrumbsContainer = document.querySelector('.o_control_panel_breadcrumbs');
        if (!breadcrumbsContainer) return;
        
        // Check if any existing button is present and remove it
        const existingButton = document.getElementById('diesel_tanker_kanban_button') || 
                             document.getElementById('diesel_tanker_progress_button');
        if (existingButton) {
            existingButton.remove();
        }

        // Create button container
        const buttonEl = document.createElement('div');
        buttonEl.id = 'diesel_tanker_kanban_button';
        buttonEl.className = 'ms-3';
        buttonEl.style.cursor = 'pointer';
        
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
        
        // Use the common button HTML function
        buttonEl.innerHTML = createDieselTankerButtonHTML(tankerData);
        
        // Insert button in breadcrumbs container
        breadcrumbsContainer.appendChild(buttonEl);
        
        // Set global flag to true
        dieselTankerButtonAdded = true;
    }, 500);
}
});