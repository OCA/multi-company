/* Copyright 2022 CreuBlanca
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define("multicompany_configuration.MulticompanyDataField", function (require) {
    "use strict";
    const BasicModel = require("web.BasicModel");
    var AbstractField = require("web.AbstractField");
    var fieldRegistry = require("web.field_registry");
    var fieldRegistryOwl = require("web.field_registry_owl");
    const FieldWrapper = require("web.FieldWrapper");
    var fieldUtils = require("web.field_utils");

    var MulticompanyDataField = AbstractField.extend({
        className: "o_multicompany_data",
        custom_events: _.extend({}, AbstractField.prototype.custom_events, {
            field_changed: "_onFieldChanged",
        }),
        init: function () {
            this._super.apply(this, arguments);
            this.BasicModel = new BasicModel(this.model);
        },
        isSet: function () {
            return true;
        },
        isValid: function () {
            return true;
        },
        _onFieldChanged: function (ev) {
            if (this.record.id === ev.data.dataPointID) {
                return;
            }
            ev.stopPropagation();
            var changes = {};
            var self = this;
            _.each(ev.data.changes, function (change, fieldName) {
                changes[fieldName] = change;
                if (change && self.value.fields[fieldName].type === "many2one") {
                    changes[fieldName] = [change.id, change.display_name];
                }
            });
            var value = {...this.value};
            value.data[this.datapoints[ev.data.dataPointID]] = {
                ...value.data[this.datapoints[ev.data.dataPointID]],
                ...changes,
            };
            this._setValue(value, {forceChange: true});
        },
        _parseValue: function (value) {
            return value;
        },
        _isSameValue: function (value) {
            return JSON.stringify(this.value) === JSON.stringify(value);
        },
        _render: function () {
            this.$el.empty();
            var self = this;
            this.datapoints = {};
            this.fieldsInfo = {
                form: Object.fromEntries(
                    _.map(self.value.fields, function (field, fieldName) {
                        var FieldWidget = undefined;
                        if (field.attrs.widget) {
                            FieldWidget =
                                fieldRegistryOwl.getAny([
                                    "form." + field.attrs.widget,
                                    field.attrs.widget,
                                ]) ||
                                fieldRegistry.getAny([
                                    "form." + field.attrs.widget,
                                    field.attrs.widget,
                                ]);
                            if (!FieldWidget) {
                                console.warn(
                                    "Missing widget: ",
                                    field.attrs.widget,
                                    " for field",
                                    fieldName,
                                    "of type",
                                    field.type
                                );
                            }
                        }
                        return [
                            fieldName,
                            {
                                ...self.record.fields[fieldName],
                                ...field,
                                Widget:
                                    FieldWidget ||
                                    fieldRegistryOwl.getAny([
                                        "form." + field.type,
                                        field.type,
                                        "abstract",
                                    ]) ||
                                    fieldRegistry.getAny([
                                        "form." + field.type,
                                        field.type,
                                        "abstract",
                                    ]),
                            },
                        ];
                    })
                ),
            };
            var mode = this.mode;
            var defs = [];
            _.each(this.value.companies, function (company) {
                var $result = $("<table/>", {class: "o_group o_inner_group"});
                var $tbody = $("<tbody />").appendTo($result);
                var col = "2";
                var $sep = $(
                    '<tr><td colspan="' +
                        col +
                        '" style="width: 100%;"><div class="o_horizontal_separator">' +
                        company[1] +
                        "</div></td></tr>"
                );
                $tbody.append($sep);
                var context = {
                    ...self.record.context,
                    company_id: company[0],
                    current_company_id: company[0],
                };
                var company_data = Object.fromEntries(
                    _.map(self.value.data[company[0]], function (value, fieldName) {
                        var type = self.fieldsInfo.form[fieldName].type;
                        if (type === "float" || type === "integer") {
                            return [fieldName, value];
                        }
                        if (
                            type === "many2one" &&
                            self.fieldsInfo.form[fieldName].attrs.widget === "selection"
                        ) {
                            return [fieldName, fieldUtils.parse[type](value)];
                        }
                        if (type !== "many2one" || !value) {
                            return [fieldName, fieldUtils.parse[type](value)];
                        }
                        var datapoint = self.BasicModel._makeDataPoint({
                            data: fieldUtils.parse[type](value),
                            fields: {},
                            modelName: self.fieldsInfo.form[fieldName].relation,
                            id: value[0],
                            type: "record",
                            context: context,
                            viewType: "form",
                        });
                        return [fieldName, datapoint];
                    })
                );
                var record = self.BasicModel._makeDataPoint({
                    fields: self.record.fields,
                    fieldsInfo: self.fieldsInfo,
                    data: {
                        ...self.record.data,
                        ...company_data,
                    },
                    modelName: "multicompany.record",
                    id: self.record.id,
                    type: "record",
                    context: context,
                    viewType: "form",
                });
                self.datapoints[record.id] = company[0];
                record.modelName = self.model;
                _.each(self.value.fields, function (field, fieldName) {
                    var $currentRow = $("<tr/>");
                    $currentRow.appendTo($tbody);
                    var $tds = $("<td/>");
                    var $label = $("<td/>", {class: "o_td_label"}).appendTo(
                        $currentRow
                    );
                    $label.append(
                        $("<label>", {
                            class: "o_form_label",
                            for: fieldName,
                            text: self.fieldsInfo.form[fieldName].string,
                        })
                    );
                    $tds.appendTo($currentRow);

                    var Widget = self.fieldsInfo.form[fieldName].Widget;
                    const legacy = !(Widget.prototype instanceof owl.Component);
                    const widgetOptions = {
                        mode: mode,
                        viewType: "form",
                        context: context,
                    };
                    var widget = undefined;
                    var def = undefined;
                    if (legacy) {
                        widget = new Widget(self, fieldName, record, widgetOptions);
                        def = widget._widgetRenderAndInsert(function () {}); // eslint-disable-line
                    } else {
                        widget = new FieldWrapper(self, Widget, {
                            fieldName,
                            record,
                            options: widgetOptions,
                        });
                        def = widget.mount(document.createDocumentFragment());
                    }
                    var $FieldEl = $("<div>");
                    defs.push(def);
                    def.then(function () {
                        widget.$el.addClass($FieldEl.attr("class"));
                        $FieldEl.replaceWith(widget.$el);
                    });
                    $tds.append($FieldEl);
                });
                // El.text(company[1]);
                self.$el.append($result);
            });

            return Promise.all(defs);
        },
    });
    fieldRegistry.add("multicompany_data", MulticompanyDataField);

    return MulticompanyDataField;
});
