/** @odoo-module **/

import {Dialog} from "@web/core/dialog/dialog";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {session} from "@web/session";
import {useHotkey} from "@web/core/hotkeys/hotkey_hook";
import {useService} from "@web/core/utils/hooks";

import {useState} from "@odoo/owl";

export class SingleActiveCompanyDialog extends Dialog {
    setup() {
        super.setup();
        // The standard dialog closes on Escape and on the header button.
        // This assignment keeps the dialog open until Confirm.
        this.data.close = () => {
            // Confirm is the only way to leave this dialog.
        };
        useHotkey("escape", () => {
            // Escape must not close this dialog.
        });
        this.orm = useService("orm");
        this.companyService = useService("company");
        this.dialogTitle = _t("Select one active company");
        this.dialogBody = _t(
            "You have more than one active company. Select one company."
        );
        this.confirmLabel = _t("Confirm");
        this.state = useState({
            selectedCompanyId: false,
            confirming: false,
        });
        this.companies = this.companyService.allowedCompanyIds
            .map((companyId) => this.companyService.availableCompanies[companyId])
            .filter(Boolean)
            .sort((companyA, companyB) => companyA.sequence - companyB.sequence);
    }

    selectCompany(companyId) {
        this.state.selectedCompanyId = companyId;
    }

    async confirm() {
        if (!this.state.selectedCompanyId || this.state.confirming) {
            return;
        }
        this.state.confirming = true;
        try {
            await this.orm.call("res.users", "apply_single_active_company", [
                this.state.selectedCompanyId,
            ]);
            this.companyService.setCompanies("loginto", this.state.selectedCompanyId);
        } catch (error) {
            this.state.confirming = false;
            throw error;
        }
    }
}

SingleActiveCompanyDialog.template =
    "res_users_single_active_company.SingleActiveCompanyDialog";
SingleActiveCompanyDialog.props = {
    ...Dialog.props,
    close: Function,
    slots: {type: Object, optional: true},
};
SingleActiveCompanyDialog.defaultProps = {
    ...Dialog.defaultProps,
    size: "md",
    contentClass: "o_single_active_company_dialog",
};

export const singleActiveCompanyService = {
    dependencies: ["company", "dialog", "orm"],
    start(_env, {company, dialog}) {
        if (session.allow_single_company && company.allowedCompanyIds.length > 1) {
            dialog.add(SingleActiveCompanyDialog, {});
        }
    },
};

registry.category("services").add("single_active_company", singleActiveCompanyService);
