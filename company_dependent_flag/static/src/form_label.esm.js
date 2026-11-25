/** @odoo-module **/

/* Copyright 2026 Simone Rubino - PyTech
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {FormLabel} from "@web/views/form/form_label";
import {patch} from "@web/core/utils/patch";

patch(FormLabel.prototype, "company_dependent_flag", {
    get CompanyDependentClasses() {
        const props = this.props;
        return props.record.fields[props.fieldName].company_dependent_css_class;
    },
});
