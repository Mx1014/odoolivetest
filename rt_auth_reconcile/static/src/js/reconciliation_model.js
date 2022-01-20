odoo.define('rt_auth_reconcile.auth_reconcile_model', function (require) {
    "use strict";

    var ReconciliationModel = require('account.ReconciliationModel');

    ReconciliationModel.StatementModel.include({
        addProposition: function (handle, mv_line_id) {
            var self = this;
            var line = this.getLine(handle);
            var prop = _.clone(_.find(line['mv_lines_'+line.mode], {'id': mv_line_id}));
            this._addProposition(line, prop);
            line['mv_lines_'+line.mode] = _.filter(line['mv_lines_'+line.mode], l => l['id'] != mv_line_id);

            line.reconciliation_proposition = _.filter(line.reconciliation_proposition, function (prop) {return prop && !prop.invalid;});

            if(!line.st_line.partner_id && line.reconciliation_proposition
                && line.reconciliation_proposition.length == 1 && prop.partner_id && line.type === undefined){
                return this.changePartner(handle, {'id': prop.partner_id, 'display_name': prop.partner_name}, true);
                }
            if(!line.st_line.x_auth && line.reconciliation_proposition
                && line.reconciliation_proposition.length == 1 && prop.x_auth && line.type === undefined){
                return this.changeAuth(handle, {'id': prop.x_auth}, true);
                }
            if(!line.st_line.x_benefit_pay_ref && line.reconciliation_proposition
                && line.reconciliation_proposition.length == 1 && prop.x_benefit_pay_ref && line.type === undefined){
                return this.changeXbenefitpayref(handle, {'id': prop.x_benefit_pay_ref}, true);
                }
            return Promise.all([
                this._computeLine(line),
                this._performMoveLine(handle, 'match_rp', line.mode == 'match_rp'? 1 : 0),
                this._performMoveLine(handle, 'match_other', line.mode == 'match_other'? 1 : 0)
                ]);
            },
        changeAuth: function (handle, auth, preserveMode) {
            var self = this;
            var line = this.getLine(handle);
            line.st_line.x_auth = auth;
            self.modes.filter(x => x.startsWith('match')).forEach(function (mode) {
                line["mv_lines_"+mode] = [];
                });

            return Promise.resolve(auth && this._changeAuth(handle, auth)).then(function(ret) {
                if(line.st_line.x_auth){
                    _.each(line.reconciliation_proposition, function(prop){
                        if(prop.x_auth != line.st_line.x_auth){
                            line.reconciliation_proposition = [];
                            return false;
                            }
                        });
                    }
                if(ret == "Not Found"){
                    line.st_line.x_auth = "";
                    }
                return self._computeLine(line);
                }).then(function () {
                    return self.changeMode(handle, preserveMode ? line.mode : 'default', true);
                    })
            },
        changeXbenefitpayref: function (handle, benefir_ref, preserveMode) {
            var self = this;
            var line = this.getLine(handle);
            line.st_line.x_benefit_pay_ref = benefir_ref;
            self.modes.filter(x => x.startsWith('match')).forEach(function (mode) {
                line["mv_lines_"+mode] = [];
                });

            return Promise.resolve(benefir_ref && this._changeXbenefitpayref(handle, benefir_ref)).then(function(ret) {
                if(line.st_line.x_benefit_pay_ref){
                    _.each(line.reconciliation_proposition, function(prop){
                        if(prop.x_benefit_pay_ref != line.st_line.x_benefit_pay_ref){
                            line.reconciliation_proposition = [];
                            return false;
                            }
                        });
                    }
                if(ret == "Not Found"){
                    line.st_line.x_benefit_pay_ref = "";
                    }
                return self._computeLine(line);
                }).then(function () {
                    return self.changeMode(handle, preserveMode ? line.mode : 'default', true);
                    })
            },
        _changeAuth: async function (handle, auth_code) {
            var self = this;
            return this._rpc({
                model: 'account.payment',
                method: 'get_partnerid_by_auth',
                args: [auth_code],
                }).then(function (result) {
                    if (result == "Not Found") {
                        var html = "<div style='border:2px solid red;padding: 4px 8px;'>Payment with that Auth code <b>'"+auth_code+"'</b> not found</div>";
                        $(".danger-alert-space").html(html);
                        return "Not Found";
                        }
                    else{
                        $(".danger-alert-space").html('');
                        self.changePartner(handle, result.partner_id);
                        return "OK";
                        }
                    });
            },
        _changeXbenefitpayref: async function (handle, x_benefit_pay_ref) {
            var self = this;
            return this._rpc({
                model: 'account.payment',
                method: 'get_partnerid_by_benefit',
                args: [x_benefit_pay_ref],
                }).then(function (result) {
                    if (result == "Not Found") {
                        var html = "<div style='border:2px solid red;padding: 4px 8px;'>Payment with that Benefit Pay code <b>'"+x_benefit_pay_ref+"'</b> not found</div>";
                        $(".danger-alert-space").html(html);
                        return "Not Found";
                        }
                    else{
                        $(".danger-alert-space").html('');
                        self.changePartner(handle, result.partner_id);
                        return "OK";
                        }
                });
            },
        removeProposition: function (handle, id) {
            var self = this;
            var line = this.getLine(handle);
            var defs = [];
            var prop = _.find(line.reconciliation_proposition, {'id' : id});
            if (prop) {
                line.reconciliation_proposition = _.filter(line.reconciliation_proposition, function (p) {
                    return p.id !== prop.id && p.id !== prop.link && p.link !== prop.id && (!p.link || p.link !== prop.link);
                    });
                if (prop['reconcileModelId'] === undefined) {
                    if (['receivable', 'payable', 'liquidity'].includes(prop.account_type)) {
                        line.mv_lines_match_rp.unshift(prop);
                        }
                    else {
                        line.mv_lines_match_other.unshift(prop);
                        }
                    }
                }
            line.mode = (id || line.mode !== "create") && isNaN(id) ? 'create' : 'match_rp';
            line.st_line.is_removed = 'Remove';
            defs.push(this._computeLine(line));
            return Promise.all(defs).then(function() {
                return self.changeMode(handle, line.mode, true);
                })
            },
        changeOffset: function (handle) {
            var line = this.getLine(handle);
            return this._performMoveLine(handle, line.mode);
            },
        _performMoveLine: function (handle, mode, limit) {
            limit = limit || this.limitMoveLines;
            var line = this.getLine(handle);
            var excluded_ids = _.map(_.union(line.reconciliation_proposition, line.mv_lines_match_rp, line.mv_lines_match_other), function (prop) {
                return _.isNumber(prop.id) ? prop.id : null;
            }).filter(id => id != null);
            var filter = line['filter_'+mode] || "";
            return this._rpc({
                    model: 'account.reconciliation.widget',
                    method: 'get_move_lines_for_bank_statement_line',
                    args: [line.id, line.st_line.partner_id, line.st_line.x_auth, line.st_line.x_benefit_pay_ref, excluded_ids, filter, 0, limit, mode === 'match_rp' ? 'rp' : 'other'],
                    context: this.context,
                    }).then(this._formatMoveLine.bind(this, handle, mode));
            },
        });
    });