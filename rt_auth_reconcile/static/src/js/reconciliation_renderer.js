odoo.define('rt_auth_reconcile.auth_reconcile', function (require) {
    "use strict";

    var ReconciliationRenderer = require('account.ReconciliationRenderer');
    var session = require('web.session');
    var Widget = require('web.Widget');
    var FieldManagerMixin = require('web.FieldManagerMixin');
    var relational_fields = require('web.relational_fields');
    var basic_fields = require('web.basic_fields');
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;

    ReconciliationRenderer.LineRenderer.include({
        events: _.extend(
            {},
            ReconciliationRenderer.LineRenderer.prototype.events,
                { 'change input[name="x_auth"]': '_onFieldChanged', 'change input[name="x_benefit_pay_ref"]': '_onFieldChanged' }
            ),
        start: function () {
            var self = this;

            var def10= this._makeAuthRecord(this._initialState.st_line.x_auth).then(function (recordID) {
                self.fields = {
                    x_auth : new basic_fields.FieldChar(self,
                        'x_auth',
                        self.model.get(recordID), {
                            mode: 'edit',
                            attrs: {
                                placeholder: _t('Enter Auth Code'),
                                }
                            })
                    };
                self.fields.x_auth.insertAfter(self.$('.accounting_view caption .o_buttons'));
                });
            var def11= this._makeBenefitPayRef(this._initialState.st_line.x_benefit_pay_ref).then(function (recordID) {
                self.fields = {
                    x_benefit_pay_ref : new basic_fields.FieldChar(self,
                        'x_benefit_pay_ref',
                        self.model.get(recordID), {
                            mode: 'edit',
                            attrs: {
                                placeholder: _t('Enter BenefitPay Ref'),
                                }
                            })
                    };
                self.fields.x_benefit_pay_ref.insertAfter(self.$('.accounting_view caption .o_buttons'));
                });

            var def2 = this._super.apply(this, arguments);
            return Promise.all([def2, def10, def11]);
            },
        update: function (state) {
            var self = this;
            var to_select = -9;
            var to_check_checked = !!(state.to_check);
            this.$('caption .o_buttons button.o_validate').toggleClass('d-none', !!state.balance.type && !to_check_checked);
            this.$('caption .o_buttons button.o_reconcile').toggleClass('d-none', state.balance.type <= 0 || to_check_checked);
            this.$('caption .o_buttons .o_no_valid').toggleClass('d-none', state.balance.type >= 0 || to_check_checked);
            self.$('caption .o_buttons button.o_validate').toggleClass('text-warning', to_check_checked);

            this._makePartnerRecord(state.st_line.partner_id, state.st_line.partner_name).then(function (recordID) {
                self.fields.partner_id.reset(self.model.get(recordID));
                self.$el.attr('data-partner', state.st_line.partner_id);
                });

            this._makeAuthRecord(state.st_line.x_auth).then(function (recordID) {
                self.$el.attr('data-partner', state.st_line.x_auth);
                });
            this._makeBenefitPayRef(state.st_line.x_benefit_pay_ref).then(function (recordID) {
                self.$el.attr('data-partner', state.st_line.x_benefit_pay_ref);
                });

            this.$el.data('mode', state.mode).attr('data-mode', state.mode);
            this.$('.o_notebook li a').attr('aria-selected', false);
            this.$('.o_notebook li a').removeClass('active');
            this.$('.o_notebook .tab-content .tab-pane').removeClass('active');
            this.$('.o_notebook li a[href*="notebook_page_' + state.mode + '"]').attr('aria-selected', true);
            this.$('.o_notebook li a[href*="notebook_page_' + state.mode + '"]').addClass('active');
            this.$('.o_notebook .tab-content .tab-pane[id*="notebook_page_' + state.mode + '"]').addClass('active');
            this.$('.create, .match').each(function () {
                $(this).removeAttr('style');
                });

            var $props = this.$('.accounting_view tbody').empty();

            var props = [];
            var balance = state.balance.amount_currency;
            _.each(state.reconciliation_proposition, function (prop) {
                if (prop.display) {
                    props.push(prop);
                    }
                });

            _.each(props, function (line) {
                if(state.st_line.x_auth){
                    if(state.st_line.x_auth.trim() != '' && state.st_line.x_auth != line.x_auth){
                        return;
                        }
                    }
                if(state.st_line.x_benefit_pay_ref){
                    if(state.st_line.x_benefit_pay_ref.trim() != '' && state.st_line.x_benefit_pay_ref != line.x_benefit_ref){
                        return;
                        }
                    }

                var $line = $(qweb.render("reconciliation.line.mv_line", {'line': line, 'state': state, 'proposition': true}));
                if (!isNaN(line.id)) {
                    $('<span class="line_info_button fa fa-info-circle"/>')
                        .appendTo($line.find('.cell_info_popover'))
                        .attr("data-content", qweb.render('reconciliation.line.mv_line.details', {'line': line}));
                    }
                $props.append($line);
                });

            var matching_modes = self.model.modes.filter(x => x.startsWith('match'));
            for (let i = 0; i < matching_modes.length; i++) {
                var stateMvLines = state['mv_lines_'+matching_modes[i]] || [];
                var recs_count = stateMvLines.length > 0 ? stateMvLines[0].recs_count : 0;
                var remaining = state['remaining_' + matching_modes[i]];
                var $mv_lines = this.$('div[id*="notebook_page_' + matching_modes[i] + '"] .match table tbody').empty();
                this.$('.o_notebook li a[href*="notebook_page_' + matching_modes[i] + '"]').parent().toggleClass('d-none', stateMvLines.length === 0 && !state['filter_'+matching_modes[i]]);

                _.each(stateMvLines, function (line) {
                    if(state.st_line.x_auth){
                        if(state.st_line.x_auth.trim() != '' && state.st_line.x_auth != line.x_auth){
                            return;
                            }
                        else{
                            to_select = line.id;
                            }
                        }
                    if(state.st_line.x_benefit_pay_ref){
                        if(state.st_line.x_benefit_pay_ref.trim() != '' && state.st_line.x_benefit_pay_ref != line.x_benefit_ref){
                            return;
                            }
                        else{
                            to_select = line.id;
                            }
                        }
                    if(to_select == -9){
                        var $line = $(qweb.render("reconciliation.line.mv_line", {'line': line, 'state': state}));
                        if (!isNaN(line.id)) {
                            $('<span class="line_info_button fa fa-info-circle"/>')
                            .appendTo($line.find('.cell_info_popover'))
                            .attr("data-content", qweb.render('reconciliation.line.mv_line.details', {'line': line}));
                            }
                        $mv_lines.append($line);
                        }
                    else if(state.st_line.is_removed && line.id == to_select){
                        var $line = $(qweb.render("reconciliation.line.mv_line", {'line': line, 'state': state}));
                        if (!isNaN(line.id)) {
                            $('<span class="line_info_button fa fa-info-circle"/>')
                            .appendTo($line.find('.cell_info_popover'))
                            .attr("data-content", qweb.render('reconciliation.line.mv_line.details', {'line': line}));
                            }
                        $mv_lines.append($line);
                        to_select = -9;
                        remaining = 0;
                        return;
                        }
                    });
                this.$('div[id*="notebook_page_' + matching_modes[i] + '"] .match div.load-more').toggle(remaining > 0);
                this.$('div[id*="notebook_page_' + matching_modes[i] + '"] .match div.load-more span').text(remaining);
                }

            this.$('.popover').remove();
            this.$('table tfoot').html(qweb.render("reconciliation.line.balance", {'state': state}));
            if (to_select != -9 && state.mode != 'inactive' && $(".accounting_view .mv_line[data-line-id='"+to_select+"']").length == 0){
                this.trigger_up('add_proposition', {'data': to_select});
                }
            if(state.st_line.is_removed){
                delete state.st_line.is_removed;
                }
            if (state.createForm) {
                var createPromise;
                if (!this.fields.account_id) {
                    createPromise = this._renderCreate(state);
                }
                Promise.resolve(createPromise).then(function(){
                    var data = self.model.get(self.handleCreateRecord).data;
                    return self.model.notifyChanges(self.handleCreateRecord, state.createForm)
                        .then(function () {
                        // FIXME can't it directly written REPLACE_WITH ids=state.createForm.analytic_tag_ids
                            return self.model.notifyChanges(self.handleCreateRecord, {analytic_tag_ids: {operation: 'REPLACE_WITH', ids: []}})
                        })
                        .then(function (){
                            var defs = [];
                            _.each(state.createForm.analytic_tag_ids, function (tag) {
                                defs.push(self.model.notifyChanges(self.handleCreateRecord, {analytic_tag_ids: {operation: 'ADD_M2M', ids: tag}}));
                            });
                            return Promise.all(defs);
                        })
                        .then(function () {
                            return self.model.notifyChanges(self.handleCreateRecord, {tax_ids: {operation: 'REPLACE_WITH', ids: []}})
                        })
                        .then(function (){
                            var defs = [];
                            _.each(state.createForm.tax_ids, function (tag) {
                                defs.push(self.model.notifyChanges(self.handleCreateRecord, {tax_ids: {operation: 'ADD_M2M', ids: tag}}));
                            });
                            return Promise.all(defs);
                        })
                        .then(function () {
                            var record = self.model.get(self.handleCreateRecord);
                            _.each(self.fields, function (field, fieldName) {
                                if (self._avoidFieldUpdate[fieldName]) return;
                                if (fieldName === "partner_id") return;

                                if ((data[fieldName] || state.createForm[fieldName]) && !_.isEqual(state.createForm[fieldName], data[fieldName])) {
                                    field.reset(record);
                                }
                                if (fieldName === 'tax_ids') {
                                    if (!state.createForm[fieldName].length || state.createForm[fieldName].length > 1) {
                                        $('.create_force_tax_included').addClass('d-none');
                                    }
                                    else {
                                        $('.create_force_tax_included').removeClass('d-none');
                                        var price_include = state.createForm[fieldName][0].price_include;
                                        var force_tax_included = state.createForm[fieldName][0].force_tax_included;
                                        self.$('.create_force_tax_included input').prop('checked', force_tax_included);
                                        self.$('.create_force_tax_included input').prop('disabled', price_include);
                                    }
                                }
                            });
                            if (state.to_check) {
                                self.$('.create_to_check input').prop('checked', state.to_check).change();
                            }
                            return true;
                        });
                    });
                }
            this.$('.create .add_line').toggle(!!state.balance.amount_currency);
            },
        _makeAuthRecord: function (authCode) {
            var field = {
                relation: 'account.bank.statement.line',
                type: 'char',
                name: 'x_auth'
                };
            if (authCode) {
                field.value = authCode;
                }
            return this.model.makeRecord('account.bank.statement.line', [field], {
                x_auth: {
                    options: {
                        no_open: true
                        }
                    }
                });
            },
        _makeBenefitPayRef: function (benefitPayRef) {
            var field = {
                relation: 'account.bank.statement',
                type: 'char',
                name: 'x_benefit_pay_ref',
                };
            if (benefitPayRef) {
                field.value = benefitPayRef;
                }
            return this.model.makeRecord('account.bank.statement.line', [field], {
                x_benefit_pay_ref: {
                    options: {
                        no_open: true
                        }
                    }
                });
            },
        _renderCreate: function (state) {
            var self = this;
            return this.model.makeRecord('account.bank.statement.line', [{
                relation: 'account.account',
                type: 'many2one',
                name: 'account_id',
                domain: [['company_id', '=', state.st_line.company_id], ['deprecated', '=', false]],
                }, {
                relation: 'account.journal',
                type: 'many2one',
                name: 'journal_id',
                domain: [['company_id', '=', state.st_line.company_id]],
                }, {
                relation: 'account.tax',
                type: 'many2many',
                name: 'tax_ids',
                domain: [['company_id', '=', state.st_line.company_id]],
                }, {
                relation: 'account.analytic.account',
                type: 'many2one',
                name: 'analytic_account_id',
                }, {
                relation: 'account.analytic.tag',
                type: 'many2many',
                name: 'analytic_tag_ids',
                }, {
                type: 'boolean',
                name: 'force_tax_included',
                }, { type: 'char', name: 'label' },{
                type: 'char',
                name: 'x_auth',
                },{
                type: 'char',
                name: 'x_benefit_pay_ref',
                },{
                type: 'float',
                name: 'amount',
                }, {
                type: 'char', //TODO is it a bug or a feature when type date exists ?
                name: 'date',
                }, {
                type: 'boolean',
                name: 'to_check',
                }],{
                account_id: {
                    string: _t("Account"),
                },
                label: {string: _t("Label")},
                amount: {string: _t("Account")},
            }).then(function (recordID) {
                self.handleCreateRecord = recordID;
                var record = self.model.get(self.handleCreateRecord);

                self.fields.account_id = new relational_fields.FieldMany2One(self,
                    'account_id', record, {mode: 'edit', attrs: {can_create:false}});

                self.fields.journal_id = new relational_fields.FieldMany2One(self,
                    'journal_id', record, {mode: 'edit'});

                self.fields.tax_ids = new relational_fields.FieldMany2ManyTags(self,
                    'tax_ids', record, {mode: 'edit', additionalContext: {append_type_to_tax_name: true}});

                self.fields.analytic_account_id = new relational_fields.FieldMany2One(self,
                    'analytic_account_id', record, {mode: 'edit'});

                self.fields.analytic_tag_ids = new relational_fields.FieldMany2ManyTags(self,
                    'analytic_tag_ids', record, {mode: 'edit'});

                self.fields.force_tax_included = new basic_fields.FieldBoolean(self,
                    'force_tax_included', record, {mode: 'edit'});

                self.fields.label = new basic_fields.FieldChar(self,
                    'label', record, {mode: 'edit'});

                self.fields.x_auth = new basic_fields.FieldChar(self,
                    'x_auth', record, {mode: 'edit'});

                self.fields.x_benefit_pay_ref = new basic_fields.FieldChar(self,
                    'x_benefit_pay_ref', record, {mode: 'edit'});

                self.fields.amount = new basic_fields.FieldFloat(self,
                    'amount', record, {mode: 'edit'});

                self.fields.date = new basic_fields.FieldDate(self,
                    'date', record, {mode: 'edit'});

                self.fields.to_check = new basic_fields.FieldBoolean(self,
                    'to_check', record, {mode: 'edit'});

                var $create = $(qweb.render("reconciliation.line.create", {'state': state, 'group_tags': self.group_tags, 'group_acc': self.group_acc}));
                self.fields.account_id.appendTo($create.find('.create_account_id .o_td_field'))
                    .then(addRequiredStyle.bind(self, self.fields.account_id));
                self.fields.journal_id.appendTo($create.find('.create_journal_id .o_td_field'));
                self.fields.tax_ids.appendTo($create.find('.create_tax_id .o_td_field'));
                self.fields.analytic_account_id.appendTo($create.find('.create_analytic_account_id .o_td_field'));
                self.fields.analytic_tag_ids.appendTo($create.find('.create_analytic_tag_ids .o_td_field'));
                self.fields.force_tax_included.appendTo($create.find('.create_force_tax_included .o_td_field'));
                self.fields.label.appendTo($create.find('.create_label .o_td_field'))
                    .then(addRequiredStyle.bind(self, self.fields.label));
                self.fields.x_auth.appendTo($create.find('.create_x_auth .o_td_field')).then(
                        addRequiredStyle.bind(self, self.fields.x_auth)
                        );
                self.fields.x_benefit_pay_ref.appendTo($create.find('.create_x_benefit_pay_ref .o_td_field'))
                    .then(addRequiredStyle.bind(self, self.fields.x_benefit_pay_ref));
                self.fields.amount.appendTo($create.find('.create_amount .o_td_field'))
                    .then(addRequiredStyle.bind(self, self.fields.amount));
                self.fields.date.appendTo($create.find('.create_date .o_td_field'));
                self.fields.to_check.appendTo($create.find('.create_to_check .o_td_field'));
                self.$('.create').append($create);

                function addRequiredStyle(widget) {
                    widget.$el.addClass('o_required_modifier');
                    }
                });
            },
        _onFieldChanged: function (event) {
            event.stopPropagation();
            var fieldName = event.target.name;
            if (fieldName === 'partner_id') {
                var partner_id = event.data.changes.partner_id;
                this.trigger_up('change_partner', {'data': partner_id});
                }
            else if (fieldName === 'x_auth') {
                var x_auth = this.$('input[name="x_auth"]').val();
                this.trigger_up('change_auth', {'data': x_auth});
                }
            else if (fieldName === 'x_benefit_pay_ref') {
                var x_benefit_pay_ref = this.$('input[name="x_benefit_pay_ref"]').val();
                this.trigger_up('change_xbenefitpayref', {'data': x_benefit_pay_ref});
                }
            else {
                if (event.data.changes.amount && isNaN(event.data.changes.amount)) {
                    return;
                    }
                this.trigger_up('update_proposition', {'data': event.data.changes});
                }
            },
        _onInputKeyup: function (event) {
            var target_partner_id = $(event.target).parents('[name="partner_id"]');
            if (target_partner_id.length === 1) {
                return;
                }
            if(event.keyCode === 13) {
                if ($(event.target).hasClass('edit_amount_input')) {
                    $(event.target).blur();
                    return;
                    }
                var created_lines = _.findWhere(this.model.lines, {mode: 'create'});
                if (created_lines && created_lines.balance.amount) {
                    this._onCreateProposition();
                    }
                return;
                }
            if ($(event.target).hasClass('edit_amount_input')) {
                if (event.type === 'keyup') {
                    return;
                    }
                else {
                    return this._editAmount(event);
                    }
                }

            var self = this;
            for (var fieldName in this.fields) {
                var field = this.fields[fieldName];
                if (!field.$el.is(event.target)) {
                    continue;
                    }
                this._avoidFieldUpdate[field.name] = event.type !== 'focusout';
                field.value = false;
                field._setValue($(event.target).val()).then(function () {
                    self._avoidFieldUpdate[field.name] = false;
                    });
                break;
                }
            },
        });
    });