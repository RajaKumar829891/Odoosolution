odoo.define('uniform_management.dashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var session = require('web.session');

    var UniformDashboard = AbstractAction.extend({
        template: 'UniformDashboard',
        events: {
            'click .o_uniform_action': '_onUniformActionClick',
        },

        /**
         * @override
         */
        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.actionManager = parent;
            this.action = action;
            this.context = action.context || {};
        },

        /**
         * @override
         */
        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return self._loadDashboardData();
            });
        },

        /**
         * @override 
         */
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._renderStats();
                self._renderCharts();
            });
        },

        /**
         * Load dashboard data
         */
        _loadDashboardData: function () {
            var self = this;
            return rpc.query({
                model: 'uniform.assignment',
                method: 'get_dashboard_data',
                args: [],
                context: session.user_context,
            }).then(function (result) {
                self.dashboardData = result;
            });
        },

        /**
         * Render statistics widgets
         */
        _renderStats: function () {
            var stats = this.dashboardData.stats || {
                total_assigned: 0,
                pending_returns: 0,
                low_stock_items: 0
            };

            // Update stats in the DOM
            this.$('.o_uniform_assigned').text(stats.total_assigned);
            this.$('.o_uniform_pending_returns').text(stats.pending_returns);
            this.$('.o_uniform_low_stock').text(stats.low_stock_items);
        },

        /**
         * Render charts
         */
        _renderCharts: function () {
            var self = this;
            var data = this.dashboardData;

            // Category distribution chart
            var ctx1 = this.$('.o_uniform_category_chart')[0].getContext('2d');
            new Chart(ctx1, {
                type: 'pie',
                data: {
                    labels: data.category_data.labels,
                    datasets: [{
                        data: data.category_data.values,
                        backgroundColor: [
                            '#28a745', // green
                            '#007bff', // blue
                            '#ffc107', // yellow
                            '#dc3545', // red
                            '#6c757d', // gray
                            '#17a2b8', // cyan
                            '#6610f2'  // purple
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    legend: {
                        position: 'right',
                    },
                    title: {
                        display: true,
                        text: 'Uniform Categories Distribution'
                    }
                }
            });

            // Monthly assignments chart
            var ctx2 = this.$('.o_uniform_monthly_chart')[0].getContext('2d');
            new Chart(ctx2, {
                type: 'bar',
                data: {
                    labels: data.monthly_data.labels,
                    datasets: [{
                        label: 'Uniforms Assigned',
                        data: data.monthly_data.values,
                        backgroundColor: '#007bff',
                        borderColor: '#0056b3',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true
                            }
                        }]
                    },
                    title: {
                        display: true,
                        text: 'Monthly Uniform Assignments'
                    }
                }
            });
        },

        /**
         * Handle click on action buttons
         */
        _onUniformActionClick: function (ev) {
            ev.preventDefault();
            var $target = $(ev.currentTarget);
            var action = $target.data('action');
            
            this.do_action(action);
        }
    });

    core.action_registry.add('uniform_dashboard', UniformDashboard);

    return UniformDashboard;
});
