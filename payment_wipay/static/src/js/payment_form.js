/* File: static/src/js/payment_form.js */
odoo.define('payment_wipay.payment_form', function (require) {
    'use strict';

    const checkoutForm = require('payment.checkout_form');
    const manageForm = require('payment.manage_form');
    const core = require('web.core');
    const _t = core._t;

    const wipayMixin = {
        /**
         * Handle the processing of the transaction when a WiPay provider is selected.
         *
         * @private
         * @param {number} providerId - The id of the payment provider handling the transaction
         * @param {object} processingValues - The processing values of the transaction
         * @return {Promise}
         */
        _processWipayTxValues: function (providerId, processingValues) {
            if (processingValues.redirect_url) {
                // Redirect directly to the WiPay hosted page
                window.location = processingValues.redirect_url;
                return Promise.resolve();
            } else {
                this._displayError(
                    _t("Payment error"),
                    _t("We were unable to process your payment. Please try again.")
                );
                return Promise.reject();
            }
        },
    };

    checkoutForm.include(Object.assign({}, wipayMixin, {
        /**
         * Handle the post-processing of the transaction in case the transaction is successful.
         *
         * @override method from payment.checkout_form
         * @private
         * @param {string} provider - The provider of the acquirer
         * @param {number} providerId - The id of the provider handling the transaction
         * @param {object} processingValues - The processing values of the transaction
         * @return {Promise}
         */
        _processPostPayment: function (provider, providerId, processingValues) {
            if (provider !== 'wipay') {
                return this._super(...arguments);
            }
            return this._processWipayTxValues(providerId, processingValues);
        },
    }));

    manageForm.include(wipayMixin);

    return {
        wipayMixin: wipayMixin,
    };
});