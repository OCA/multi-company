/** @odoo-module **/

const {Component, onWillStart} = owl;

import {Field} from "@web/views/fields/field";
import {FormLabel} from "@web/views/form/form_label";

import {OuterGroup} from "@web/views/form/form_group/form_group";
import {registry} from "@web/core/registry";

export class MultiCompanyDataField extends Component {
    setup() {
        this.records = {};
        onWillStart(this.loadRecords);
    }
    async loadRecords() {
        for (const company of this.props.value.companies) {
            const record = this.props.record.model.createDataPoint("record", {
                resModel: this.props.record.resModel,
                fields: this.props.value.fields,
                activeFields: this.props.value.fields,
                viewType: "form",
                context: {
                    ...this.props.record.context,
                    company_id: company[0],
                    current_company_id: company[0],
                },
                rawContext: {
                    parent: {
                        ...this.props.record.rawContext,
                        company_id: company[0],
                        current_company_id: company[0],
                    },
                    make: () => {
                        return {
                            ...this.props.record.context,
                            company_id: company[0],
                            current_company_id: company[0],
                        };
                    },
                },
                resId: this.props.record.resId,
            });
            await record.load();
            record.data = this.props.value.data[company[0]];
            this.records[company[0]] = record;
        }
    }

    field_props(company, field) {
        const props = {
            name: field,
            type: this.props.value.fields[field].type,
            record: this.records[company[0]],
            update: async (value) => {
                const origin_value = this.props.value;
                if (this.props.value.fields[field].type === "many2one" && value) {
                    origin_value.data[company[0]][field] = value;
                } else {
                    origin_value.data[company[0]][field] = value;
                }
                this.props.record.update({[this.props.name]: origin_value});
                await this.records[company[0]].update({[field]: value});
            },
        };
        return props;
    }
}

MultiCompanyDataField.components = {Field, FormLabel, OuterGroup};
MultiCompanyDataField.template = "multicompany_configuration.MultiCompanyDataField";

registry.category("fields").add("multicompany_data", MultiCompanyDataField);
