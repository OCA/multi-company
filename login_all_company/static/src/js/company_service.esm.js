/** @odoo-module **/

import {companyService} from "@web/webclient/company_service";
import {cookie} from "@web/core/browser/cookie";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";

const CIDS_HASH_SEPARATOR = "-";

function parseCompanyIds(cids, separator = ",") {
    if (typeof cids === "string") {
        return cids.split(separator).map(Number);
    } else if (typeof cids === "number") {
        return [cids];
    }
    return [];
}

function formatCompanyIds(cids, separator = ",") {
    return cids.join(separator);
}

function getCompanyIdsFromBrowser(hash) {
    let cids = null;
    if ("cids" in hash) {
        cids = parseCompanyIds(hash.cids, CIDS_HASH_SEPARATOR);
    } else if (cookie.get("cids")) {
        cids = parseCompanyIds(cookie.get("cids"));
    }
    return cids || [];
}

function computeAllCompanyIds() {
    const {
        user_companies: {
            allowed_companies: availableCompaniesFromSession,
            current_company: currentCompany,
        },
    } = session;
    const cids = [];
    Object.keys(availableCompaniesFromSession)
        .map(Number)
        .forEach((cid) => {
            if (currentCompany === cid) {
                cids.unshift(cid);
            } else {
                cids.push(cid);
            }
        });

    return cids;
}

patch(companyService, {
    start(env, {router}) {
        const cids = getCompanyIdsFromBrowser(router.current.hash);
        if (!cids.length) {
            const allCids = computeAllCompanyIds(cids);
            cookie.set("cids", formatCompanyIds(allCids));
        }
        return super.start(...arguments);
    },
});
