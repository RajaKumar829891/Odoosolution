/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";

export class MyOperatorCallButton extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.actionService = useService("action");
        this.notification = useService("notification");
    }

    async makeCall() {
        try {
            const result = await this.rpc("/web/dataset/call_kw", {
                model: "res.partner",
                method: "action_make_myoperator_call",
                args: [[this.props.record.resId]],
                kwargs: {},
            });
            
            if (result && result.type === 'ir.actions.client') {
                this.notification.add(result.params.title, {
                    type: result.params.type,
                    message: result.params.message,
                });
            }
        } catch (error) {
            this.notification.add(this.env._t("Error"), {
                type: "danger",
                message: this.env._t("Failed to initiate call."),
            });
        }
    }

    async sendWhatsApp() {
        try {
            const result = await this.rpc("/web/dataset/call_kw", {
                model: "res.partner",
                method: "action_send_myoperator_whatsapp",
                args: [[this.props.record.resId]],
                kwargs: {},
            });
            
            if (result && result.type) {
                this.actionService.doAction(result);
            }
        } catch (error) {
            this.notification.add(this.env._t("Error"), {
                type: "danger",
                message: this.env._t("Failed to open WhatsApp wizard."),
            });
        }
    }
}

MyOperatorCallButton.template = "myoperator_integration.CallButtons";

registry.category("view_widgets").add("myoperator_buttons", {
    component: MyOperatorCallButton,
});