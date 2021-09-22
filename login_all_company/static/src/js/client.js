odoo.define("login_all_company.AbstractWebClient", function (require) {
    "use strict";
    var AbstractWebClient = require("web.AbstractWebClient");
    var session = require("web.session");
    var utils = require("web.utils");
    AbstractWebClient.include({
        start: function () {
            var state = $.bbq.getState();
            if (!utils.get_cookie("cids") && !state.cids) {
                var companies = [session.company_id];
                _.forEach(session.user_companies.allowed_companies, function (company) {
                    if (company[0] !== session.company_id) {
                        companies.push(company[0]);
                    }
                });
                state.cids = companies.join(",");
                $.bbq.pushState(state);
            }
            return this._super.apply(this, arguments);
        },
    });
});
