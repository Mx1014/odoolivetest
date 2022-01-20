odoo.define('rt_auth_reconcile.auth_reconcile_action', function (require) {
    "use strict";

    var ReconciliationClientAction = require('account.ReconciliationClientAction');
    var core = require('web.core');
    var _t = core._t;

    ReconciliationClientAction.StatementAction.include({
        custom_events: _.extend(
            {},
            ReconciliationClientAction.StatementAction.prototype.custom_events,
                { change_auth: '_onAction', change_xbenefitpayref: '_onAction' }
            ),
        });
    });