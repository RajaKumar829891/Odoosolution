odoo.define('simply_fleet.mobile_view', function (require) {
    'use strict';
    
    var config = require('web.config');
    var ListController = require('web.ListController');
    var KanbanController = require('web.KanbanController');
    var core = require('web.core');
    var View = require('web.View');
    
    // Override to prioritize kanban on mobile for vehicles
    if (config.device.isMobile) {
        ListController.include({
            init: function (parent, model, renderer, params) {
                this._super.apply(this, arguments);
                if (this.modelName === 'simply.fleet.vehicle') {
                    this.switchView('kanban');
                }
            },
        });
        
        // Make sure the kanban view is always initialized first for vehicles
        core.action_registry.add('simply_fleet_vehicle_kanban_action', function(parent, action) {
            action.views = _.sortBy(action.views, function(view) {
                return view[1] === 'kanban' ? -1 : 1;
            });
            return View.prototype.loadViews.call(this, parent, action);
        });
    }
});
