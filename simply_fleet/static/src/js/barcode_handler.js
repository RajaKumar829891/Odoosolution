odoo.define('simply_fleet.barcode_handler', [], function () {
    'use strict';
    
    // Using a jQuery document-ready function
    $(function() {
        $(document).on('keydown', 'input[name="barcode"]', function(event) {
            if (event.keyCode === 13) { // Enter key
                var self = this;
                // Delay to allow onchange to process
                setTimeout(function() {
                    // Find current row and next row
                    var currentRow = $(self).closest('tr');
                    var nextRow = currentRow.next('tr');
                    
                    // If there's a next row, focus on its barcode field
                    if (nextRow.length) {
                        nextRow.find('input[name="barcode"]').focus();
                    } else {
                        // If no next row, click the "Add a line" button
                        var addButton = $(self).closest('.o_field_x2many_list')
                                .find('.o_field_x2many_list_row_add a');
                        
                        if (addButton.length) {
                            addButton.click();
                            
                            // Delay to allow new row creation
                            setTimeout(function() {
                                // Focus on the barcode field of the newly created row
                                var newRow = $(self).closest('.o_field_x2many_list')
                                                 .find('tr.o_data_row:last');
                                if (newRow.length) {
                                    var barcodeField = newRow.find('input[name="barcode"]');
                                    if (barcodeField.length) {
                                        barcodeField.focus();
                                    }
                                }
                            }, 200);
                        }
                    }
                }, 200);
            }
        });
    });
    
    return {};
});
