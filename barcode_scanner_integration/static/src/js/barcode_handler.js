/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, xml } from "@odoo/owl";

export class BarcodeHandler extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = {
            barcodeInput: '',
            lastKeyPress: 0,
            timeoutVal: 50
        };
        
        this.boundKeypress = this._onKeypress.bind(this);
        document.addEventListener('keypress', this.boundKeypress);
    }

    _onKeypress(e) {
        const currentTime = new Date().getTime();
        
        if (currentTime - this.state.lastKeyPress > this.state.timeoutVal) {
            this.state.barcodeInput = '';
        }
        
        this.state.lastKeyPress = currentTime;
        
        if (e.which !== 13) {
            this.state.barcodeInput += String.fromCharCode(e.which);
        } else {
            this._processBarcode(this.state.barcodeInput);
            this.state.barcodeInput = '';
        }
    }

    async _processBarcode(barcode) {
        try {
            barcode = barcode.replace(/[\n\r]+/g, '');
            
            if (!barcode) {
                return;
            }

            const result = await this.orm.call(
                'stock.picking',
                'process_barcode_from_ui',
                [barcode]
            );

            if (result.success) {
                this._showSuccess(result.message);
            } else {
                this._showError(result.message || "Unknown error");
            }
        } catch (error) {
            this._showError(error.message || "Error processing barcode");
        }
    }

    _showSuccess(message) {
        this.notification.add(message, {
            type: "success",
        });
    }

    _showError(message) {
        this.notification.add(message, {
            type: "danger",
        });
    }

    destroy() {
        document.removeEventListener('keypress', this.boundKeypress);
    }
}

BarcodeHandler.template = xml`
    <div class="o_barcode_handler">
        <t t-slot="default"/>
    </div>
`;

registry.category("main_components").add("BarcodeHandler", {
    Component: BarcodeHandler,
});
