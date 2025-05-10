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
            // Open the file viewer
            this.fileViewer.open(attachment, attachments);
            
            // Only apply z-index fix when file viewer opens
            const applyZIndexToFileViewer = () => {
                const fileViewerSelectors = [
                    '.o_FileViewer',
                    '.o-FileViewer',
                    '[class*="FileViewer"]'
                ];
                
                let fileViewerEl = null;
                for (const selector of fileViewerSelectors) {
                    fileViewerEl = document.querySelector(selector);
                    if (fileViewerEl && window.getComputedStyle(fileViewerEl).display !== 'none') {
                        break;
                    }
                }
                
                if (fileViewerEl) {
                    // Create a unique class for our fix
                    fileViewerEl.classList.add('file-viewer-above-modal');
                    
                    // Apply inline styles that are more specific
                    fileViewerEl.style.setProperty('z-index', '2051', 'important');
                    
                    // Find any modal containing the file viewer
                    const parentModal = fileViewerEl.closest('.modal');
                    if (parentModal) {
                        parentModal.style.setProperty('z-index', '2051', 'important');
                    }
                }
            };
            
            // Apply z-index with a small delay
            setTimeout(applyZIndexToFileViewer, 200);
            
            // Clean up when file viewer closes
            const cleanupFileViewer = () => {
                const fileViewerEl = document.querySelector('.file-viewer-above-modal');
                if (fileViewerEl) {
                    fileViewerEl.classList.remove('file-viewer-above-modal');
                    fileViewerEl.style.removeProperty('z-index');
                    
                    const parentModal = fileViewerEl.closest('.modal');
                    if (parentModal) {
                        parentModal.style.removeProperty('z-index');
                    }
                }
            };
            
            // Listen for file viewer close events
            const fileViewerObserver = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList') {
                        // Check if file viewer was removed
                        const fileViewerExists = document.querySelector('.file-viewer-above-modal');
                        if (!fileViewerExists) {
                            cleanupFileViewer();
                            fileViewerObserver.disconnect();
                        }
                    }
                });
            });
            
            fileViewerObserver.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            // Disconnect observer after 30 seconds
            setTimeout(() => {
                fileViewerObserver.disconnect();
                cleanupFileViewer();
            }, 30000);
        }
    }
};

patch(Many2ManyBinaryField.prototype, Many2ManyBinaryFieldPatch);