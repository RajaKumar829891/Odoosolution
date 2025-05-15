odoo.define('myoperator_integration.myoperator_widget', ['web.core', 'web.Widget', 'web.rpc', 'web.session', 'web.SystrayMenu', 'web.Dialog'], function (require) {
    "use strict";
    
        const core = require('web.core');
        const Widget = require('web.Widget');
        const rpc = require('web.rpc');
        const _t = core._t;
        const QWeb = core.qweb;
        const session = require('web.session');
        const SystrayMenu = require('web.SystrayMenu');
        const Dialog = require('web.Dialog');
    
        const MyOperatorSystrayWidget = Widget.extend({
            template: 'MyOperatorSystray',
            events: {
                'click .o_myoperator_make_call': '_onClickMakeCall',
            },
    
            init: function () {
                this._super.apply(this, arguments);
            },
    
            _onClickMakeCall: function (ev) {
                ev.preventDefault();
                const self = this;
                
                // Create a dialog to enter phone number
                const $content = $(QWeb.render('MyOperatorCallDialog'));
                
                const dialog = new Dialog(this, {
                    title: _t('Make a Call'),
                    $content: $content,
                    buttons: [{
                        text: _t('Call'),
                        classes: 'btn-primary',
                        click: function () {
                            const phone = $content.find('input[name="phone"]').val();
                            if (!phone) {
                                Dialog.alert(this, _t('Please enter a phone number'));
                                return;
                            }
                            
                            // Call the server to initiate call
                            rpc.query({
                                model: 'myoperator.call',
                                method: 'make_call',
                                args: [phone],
                            }).then(function(result) {
                                if (result.status === 'success') {
                                    self.displayNotification({
                                        title: _t('Call Initiated'),
                                        message: result.message,
                                        type: 'success',
                                    });
                                } else {
                                    self.displayNotification({
                                        title: _t('Call Failed'),
                                        message: result.message,
                                        type: 'warning',
                                    });
                                }
                            }).guardedCatch(function (error) {
                                self.displayNotification({
                                    title: _t('Error'),
                                    message: _t('Failed to initiate call.'),
                                    type: 'danger',
                                });
                            });
                            dialog.close();
                        }
                    }, {
                        text: _t('Cancel'),
                        close: true,
                    }]
                });
                
                dialog.open();
            }
        });
    
        // Add the widget to the systray menu
        SystrayMenu.Items.push(MyOperatorSystrayWidget);
    
        return MyOperatorSystrayWidget;
    });