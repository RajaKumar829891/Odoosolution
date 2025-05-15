/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

const systrayRegistry = registry.category("systray");

class MyOperatorCallDialog extends Component {
    setup() {
        this.state = useState({
            phone: '',
        });
        this.rpc = useService("rpc");
        this.notification = useService("notification");
    }

    async makeCall() {
        if (!this.state.phone) {
            this.notification.add(this.env._t("Please enter a phone number"), {
                type: "warning",
            });
            return;
        }

        try {
            const result = await this.rpc("/web/dataset/call_kw", {
                model: "myoperator.call",
                method: "make_call",
                args: [this.state.phone],
                kwargs: {},
            });

            if (result.status === 'success') {
                this.notification.add(this.env._t("Call Initiated"), {
                    type: "success",
                    message: result.message,
                });
            } else {
                this.notification.add(this.env._t("Call Failed"), {
                    type: "warning",
                    message: result.message,
                });
            }
        } catch (error) {
            this.notification.add(this.env._t("Error"), {
                type: "danger",
                message: this.env._t("Failed to initiate call."),
            });
        }

        this.props.close();
    }

    onPhoneInput(event) {
        this.state.phone = event.target.value;
    }
}

MyOperatorCallDialog.template = "myoperator_integration.CallDialog";
MyOperatorCallDialog.components = { Dialog };

export class MyOperatorSystrayItem extends Component {
    setup() {
        this.dialogService = useService("dialog");
    }

    openCallDialog() {
        this.dialogService.add(MyOperatorCallDialog);
    }
}

MyOperatorSystrayItem.template = "myoperator_integration.SystrayItem";

systrayRegistry.add("myoperator", {
    Component: MyOperatorSystrayItem,
});