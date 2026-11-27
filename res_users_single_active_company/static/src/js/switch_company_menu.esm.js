/** @odoo-module **/

import {SwitchCompanyMenu} from "@web/webclient/switch_company_menu/switch_company_menu";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";

patch(
    SwitchCompanyMenu.prototype,
    "res_users_single_active_company.SwitchCompanyMenu",
    {
        get isSingleActiveCompany() {
            return Boolean(session.allow_single_company);
        },

        get selectedCompanies() {
            if (this.isSingleActiveCompany) {
                const currentCompany = this.companyService.currentCompany;
                return currentCompany ? [currentCompany.id] : [];
            }
            return this._super(...arguments);
        },

        toggleCompany(companyId) {
            if (this.isSingleActiveCompany) {
                this.companyService.setCompanies("loginto", companyId);
                return;
            }
            return this._super(...arguments);
        },

        logIntoCompany(companyId) {
            if (this.isSingleActiveCompany) {
                this.companyService.setCompanies("loginto", companyId);
                return;
            }
            return this._super(...arguments);
        },
    }
);

// Class getters are not enumerable. OWL capture() copies enumerable keys
// with result[key] = ctx[key], and a getter without a setter throws.
const singleCompanyDesc = Object.getOwnPropertyDescriptor(
    SwitchCompanyMenu.prototype,
    "isSingleActiveCompany"
);
Object.defineProperty(SwitchCompanyMenu.prototype, "isSingleActiveCompany", {
    ...singleCompanyDesc,
    enumerable: false,
});
