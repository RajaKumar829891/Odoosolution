/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, onMounted, useRef } from "@odoo/owl";

export class BarcodeFieldWidget extends Component {
    static template = 'my_barcode_scanner.BarcodeFieldWidget';
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.inputRef = useRef("input");
    }

    async openScanner() {
        const workOrderId = this.props.record.resId;
        const url = `/barcode/scanner?work_order_id=${workOrderId}`;
        window.location.href = url;
    }
}

registry.category("fields").add("barcode_widget", BarcodeFieldWidget);
