/* Copyright 2026 Simone Rubino - PyTech
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {FormLabel} from "@web/views/form/form_label";
import {patch} from "@web/core/utils/patch";

patch(FormLabel.prototype, {
    get CompanyDependentClasses() {
        return this.props.fieldInfo.attrs["data-company-dep-class"];
    },
});
