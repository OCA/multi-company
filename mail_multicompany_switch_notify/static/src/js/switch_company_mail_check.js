/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { CompanySelector } from "@web/webclient/switch_company_menu/switch_company_menu";
import { browser } from "@web/core/browser/browser";

/**
 * CompanySelector.apply() is the single choke point both the "confirm"
 * (multi-select) flow and the direct "log into" click go through when a
 * company switch is applied. It always ends in a full page reload
 * (companyService.setCompanies() -> router.pushState(..., { reload: true })),
 * so any notification fired at click time would be lost. Instead we drop a
 * flag in sessionStorage here (it survives the reload) and pick it up in
 * mail_server_company_check.js once the webclient has re-mounted.
 */
patch(CompanySelector.prototype, {
    apply() {
        browser.sessionStorage.setItem("check_mail_server_after_switch", "1");
        return super.apply(...arguments);
    },
});
