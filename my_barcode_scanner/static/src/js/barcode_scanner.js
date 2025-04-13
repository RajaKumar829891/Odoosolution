/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, onMounted, useRef } from "@odoo/owl";

export class MobileBarcodeScanner extends Component {
    static template = "my_barcode_scanner.MobileBarcodeScannerTemplate";

    setup() {
        this.state = useState({
            currentScan: "",
            scanHistory: [],
            workOrderId: null,
            errorMessage: "",
            successMessage: "",
            isScanning: false
        });
        
        this.videoRef = useRef("video");
        
        // Get work order ID from URL parameters or passed params
        onMounted(() => {
            // Check if work order ID was passed via action params
            const workOrderId = this.props.work_order_id || 
                                new URLSearchParams(window.location.search).get('work_order_id');
            
            if (workOrderId) {
                this.state.workOrderId = parseInt(workOrderId);
            }
            
            this.initCamera();
        });
    }
    
    async initCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "environment" }
            });
            
            if (this.videoRef.el) {
                this.videoRef.el.srcObject = stream;
                
                // Set up a video event listener
                this.videoRef.el.addEventListener('loadedmetadata', () => {
                    // Once video is loaded, we can start scanning
                    this.setupScanner();
                });
            }
        } catch (err) {
            this.state.errorMessage = "Camera access error: " + err.message;
        }
    }
    
    setupScanner() {
        console.log("Scanner ready");
    }
    
    startScanner() {
        this.state.isScanning = true;
        this.state.errorMessage = "";
        this.state.successMessage = "";
        this.scanCode();
    }
    
    stopScanner() {
        this.state.isScanning = false;
        if (this.videoRef.el && this.videoRef.el.srcObject) {
            const tracks = this.videoRef.el.srcObject.getTracks();
            tracks.forEach(track => track.stop());
        }
    }
    
    scanCode() {
        if (!this.state.isScanning) return;
        
        // For testing purposes, prompt for a barcode
        // In a real implementation, you would use a barcode scanning library
        const barcode = prompt("Enter barcode (simulation):", "ITEM12345");
        
        if (barcode) {
            this.processScan(barcode);
        } else {
            // If canceled, continue scanning
            if (this.state.isScanning) {
                setTimeout(() => this.scanCode(), 1000);
            }
        }
    }
    
    processScan(barcode) {
        this.state.currentScan = barcode;
        
        // Add to scan history
        this.state.scanHistory.unshift({
            barcode: barcode,
            timestamp: new Date().toLocaleTimeString()
        });
        
        // Process barcode with server
        this.processServerScan(barcode);
    }
    
    async processServerScan(barcode) {
        try {
            // Use the new scan endpoint
            const response = await fetch('/barcode/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {
                        barcode_data: barcode,
                        work_order_id: this.state.workOrderId
                    },
                    id: new Date().getTime()
                })
            });
            
            // Check if response is ok
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            // Log the full result for debugging
            console.log('Barcode Scan Result:', result);
            
            if (result.error) {
                this.state.errorMessage = result.error;
                this.state.successMessage = "";
                console.error('Barcode processing error:', result.error);
            } else {
                this.state.successMessage = `Scanned: ${result.product_name}`;
                this.state.errorMessage = "";
                
                // Redirect to work order if product found and work order ID exists
                if (result.product_id && this.state.workOrderId) {
                    window.location.href = `/barcode/redirect?work_order_id=${this.state.workOrderId}&barcode=${barcode}`;
                    return;
                }
            }
        } catch (error) {
            console.error('Error processing scan:', error);
            this.state.errorMessage = "Error processing scan: " + error.message;
            this.state.successMessage = "";
        }
        
        // Continue scanning if still in scanning mode
        if (this.state.isScanning) {
            setTimeout(() => this.scanCode(), 1000);
        }
    }
    
    returnToWorkOrder() {
        if (this.state.workOrderId) {
            window.location.href = `/web#id=${this.state.workOrderId}&model=simply.vehicle.work.order&view_type=form`;
        } else {
            window.location.href = '/web';
        }
    }
    
    clearHistory() {
        this.state.scanHistory = [];
    }
}

// Register the client action
registry.category("actions").add("mobile_barcode_scanner", {
    Component: MobileBarcodeScanner,
});
