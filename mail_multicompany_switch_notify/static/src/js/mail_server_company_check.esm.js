import {Component, onMounted} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {browser} from "@web/core/browser/browser";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {user} from "@web/core/user";

/**
 * Renders nothing. Mounted once at webclient startup (including right
 * after a company-switch reload). If the sessionStorage flag set by
 * switch_company_mail_check.esm.js is present, it checks whether the newly
 * active company has an outgoing mail server configured and, if not,
 * shows a warning notification. The flag is cleared immediately so the
 * notification only ever appears once per switch, not on every
 * subsequent page load/navigation.
 */
export class MailServerCompanyCheck extends Component {
    static template = "mail_multicompany_switch_notify.MailServerCompanyCheck";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        onMounted(() => this.checkMailServer());
    }

    async checkMailServer() {
        if (!browser.sessionStorage.getItem("check_mail_server_after_switch")) {
            return;
        }
        browser.sessionStorage.removeItem("check_mail_server_after_switch");

        const currentCompany = user.activeCompany;
        if (!currentCompany) {
            return;
        }

        let hasServer = false;
        try {
            hasServer = await this.orm.call("res.company", "has_outgoing_mail_server", [
                currentCompany.id,
            ]);
        } catch (error) {
            // Never let a failed check block or spam the UI.
            browser.console.error("Mail server check failed:", error);
            return;
        }

        if (!hasServer) {
            this.notification.add(
                _t(
                    "%s has no outgoing mail server of its own. Its emails will be sent through another server and may be rejected or marked as spam.",
                    currentCompany.name
                ),
                {
                    type: "warning",
                    sticky: true,
                    title: _t("No Mail Server Configured"),
                }
            );
        }
    }
}

registry.category("main_components").add("MailServerCompanyCheck", {
    Component: MailServerCompanyCheck,
});
