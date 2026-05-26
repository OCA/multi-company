import {companyService} from "@web/webclient/company_service";
import {cookie} from "@web/core/browser/cookie";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";

patch(companyService, {
    start() {
        if (cookie && !cookie.get("cids")) {
            var companies = [session.user_companies.current_company];
            for (const company of Object.values(
                session.user_companies.allowed_companies
            )) {
                if (company.id !== session.user_companies.current_company) {
                    companies.push(company.id);
                }
            }
            cookie.set("cids", companies.join("-"));
        }
        return super.start(...arguments);
    },
});
