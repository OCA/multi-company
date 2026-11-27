/** @odoo-module **/

import {browser} from "@web/core/browser/browser";
import {companyService} from "@web/webclient/company_service";
import {patch} from "web.utils";
import {session} from "@web/session";

// The loginto mode keeps the other active companies when more than one
// company is already active. This patch stores one company id.
patch(companyService, "res_users_single_active_company.company_service", {
    start(env, dependencies) {
        const service = this._super(...arguments);
        if (!session.allow_single_company) {
            return service;
        }
        const {router, cookie} = dependencies;
        service.setCompanies = (mode, ...companyIds) => {
            const companyId = companyIds[0];
            if (!companyId) {
                return;
            }
            const cids = String(companyId);
            router.pushState({cids}, {lock: true});
            cookie.setCookie("cids", cids);
            browser.setTimeout(() => browser.location.reload());
        };
        return service;
    },
});
