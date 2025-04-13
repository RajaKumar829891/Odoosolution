/** @odoo-module */

import { Many2ManyBinaryField } from "@web/views/fields/many2many_binary/many2many_binary_field";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useFileViewer } from "@web/core/file_viewer/file_viewer_hook";

const Many2ManyBinaryFieldPatch = {
    setup() {
        super.setup(...arguments);
        this.store = useService("mail.store");
        this.fileViewer = useFileViewer();
    },
    onClickPreview({ id, name, mimetype }, files) {

        const attachments = files.map(f => this.store.Attachment.insert({
            id: f.id,
            filename: f.name,
            name: this.props.name,
            mimetype: f.mimetype,
        }));

        const attachment = attachments.find(a => a.id === id);
        if (attachment) {
            this.fileViewer.open(attachment, attachments);
        }
    }
};

patch(Many2ManyBinaryField.prototype, Many2ManyBinaryFieldPatch);
