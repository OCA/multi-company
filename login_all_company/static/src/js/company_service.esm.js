/** @odoo-module **/

import {companyService} from "@web/webclient/company_service";
import {patch} from "web.utils";
import {session} from "@web/session";

patch(companyService, "login_all_company/static/src/js/company_service.esm.js", {
    start(env, {router, cookie}) {
        if (!cookie.current.cids && !router.current.hash.cids) {
            var companies = [session.company_id];
            _.forEach(session.user_companies.allowed_companies, function (company) {
                if (company.id !== session.company_id) {
                    companies.push(company.id);
                }
            });
            cookie.setCookie("cids", companies.join(","));
        }
        return this._super(...arguments);
    },
});
