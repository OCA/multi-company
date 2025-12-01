/** @odoo-module **/

import {Component, onWillStart, useEffect, useState} from "@odoo/owl";
import {Field} from "@web/views/fields/field";
import {FormLabel} from "@web/views/form/form_label";
import {OuterGroup} from "@web/views/form/form_group/form_group";
import {registry} from "@web/core/registry";

export class MultiCompanyDataField extends Component {
    static components = {Field, FormLabel, OuterGroup};
    static template = "multicompany_configuration.MultiCompanyDataField";
    static props = {
        record: Object,
        name: String,
        readonly: {type: Boolean, optional: true},
        id: {type: String, optional: true},
    };

    setup() {
        this.records = useState({});
        this.orm = this.env.services.orm;
        this.lastSentData = null;
        onWillStart(async () => {
            await this.loadRecords();
        });
        useEffect(
            () => {
                this.loadRecords();
            },
            () => [this.props.record.data[this.props.name]]
        );
    }

    get values() {
        const val = this.props.record.data[this.props.name];
        return val ? JSON.parse(JSON.stringify(val)) : {};
    }

    async loadRecords() {
        const incomingValues = this.values;
        const companies = incomingValues.companies || [];
        const RecordClass = this.props.record.model.constructor.Record;
        const updates = {};
        for (const company of companies) {
            const companyId = company[0];
            const incomingData =
                (incomingValues.data && incomingValues.data[companyId]) || {};
            const config = {
                context: {
                    ...this.props.record.model.config.context,
                    company_id: companyId,
                    current_company_id: companyId,
                },
                activeFields:
                    incomingValues.fields ||
                    this.props.record.model.config.activeFields,
                resModel: this.props.record.resModel,
                fields: incomingValues.fields || this.props.record.fields,
                resId: this.props.record.resId || false,
                resIds: this.props.record.resId ? [this.props.record.resId] : [],
                isMonoRecord: true,
                mode: "edit",
            };

            const recordDp = new RecordClass(
                this.props.record.model,
                config,
                incomingData,
                {
                    manuallyAdded: !incomingData.id,
                    onUpdate: async () => this._onRecordUpdate(companyId),
                }
            );

            updates[companyId] = recordDp;
            Object.assign(this.records, updates);
        }
    }

    async _onRecordUpdate(companyId) {
        const values = this.values;
        const record = this.records[companyId];

        if (record && values) {
            const updatedData = {};
            for (const cId in values.data) {
                updatedData[cId] = {...values.data[cId]};
            }
            updatedData[companyId] = {...record.data};
            const newValues = {
                companies: values.companies,
                fields: values.fields,
                data: updatedData,
            };
            this.lastSentData = JSON.parse(JSON.stringify(newValues));
            this.props.record.update({[this.props.name]: newValues});
        }
    }

    field_props(company, field) {
        const values = this.values;
        if (!this.records[company[0]]) return null;

        return {
            name: field,
            type: values.fields && values.fields[field] && values.fields[field].type,
            record: this.records[company[0]],
        };
    }
}

registry.category("fields").add("multicompany_data", {
    component: MultiCompanyDataField,
});
