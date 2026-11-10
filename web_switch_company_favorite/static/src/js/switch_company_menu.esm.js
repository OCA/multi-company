import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {SwitchCompanyMenu} from "@web/webclient/switch_company_menu/switch_company_menu";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import {status} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

patch(SwitchCompanyMenu.prototype, {
    setup() {
        super.setup(...arguments);
        this.actionService = useService("action");
        this.orm = useService("orm");
        this.dialogService = useService("dialog");

        this.state.activeTab = "companies";
        this.state.favorites = [];
    },

    async handleDropdownChange(isOpen) {
        super.handleDropdownChange(isOpen);
        if (isOpen) {
            await this.loadFavorites();
        } else {
            this.state.activeTab = "companies";
        }
    },

    get userFavorites() {
        return (this.state.favorites || []).filter(
            (filter) => filter.user_ids && filter.user_ids.length > 0
        );
    },

    get sharedFavorites() {
        return (this.state.favorites || []).filter(
            (filter) => !filter.user_ids || filter.user_ids.length === 0
        );
    },

    async loadFavorites() {
        const favorites = await this.orm.call("ir.filters", "get_filters", [
            "res.company",
        ]);
        this.state.favorites = favorites;
    },

    setActiveTab(tab) {
        this.state.activeTab = tab;
        if (tab === "favorites") {
            this.loadFavorites();
        }
    },

    async applyFavoriteFilter(filter) {
        const companyIds = await this.orm.call(
            "res.company",
            "get_companies_from_filter",
            [filter.id]
        );

        // Update selection using the core switchCompany("toggle") method to trigger reactivity perfectly
        const currentSelected = [...this.companySelector.selectedCompaniesIds];
        for (const id of currentSelected) {
            if (!companyIds.includes(id)) {
                this.companySelector.switchCompany("toggle", id);
            }
        }
        for (const id of companyIds) {
            if (!this.companySelector.selectedCompaniesIds.includes(id)) {
                this.companySelector.switchCompany("toggle", id);
            }
        }
        this.state.activeTab = "companies";
    },

    createFavoriteFilter() {
        this.actionService.doAction(
            {
                type: "ir.actions.act_window",
                name: _t("Create Favorite Filter"),
                res_model: "ir.filters",
                views: [[false, "form"]],
                target: "new",
                context: {
                    default_model_id: "res.company",
                    default_user_ids: [this.user.userId],
                },
            },
            {
                onClose: async () => {
                    if (status(this) === "mounted") {
                        await this.loadFavorites();
                    }
                },
            }
        );
    },

    editFavoriteFilter(filter) {
        this.actionService.doAction(
            {
                type: "ir.actions.act_window",
                name: _t("Edit Favorite Filter"),
                res_model: "ir.filters",
                res_id: filter.id,
                views: [[false, "form"]],
                target: "new",
            },
            {
                onClose: async () => {
                    if (status(this) === "mounted") {
                        await this.loadFavorites();
                    }
                },
            }
        );
    },

    deleteFavoriteFilter(filter) {
        this.dialogService.add(ConfirmationDialog, {
            body: _t('Are you sure you want to delete the filter "%s"?', filter.name),
            confirm: async () => {
                await this.orm.call("ir.filters", "unlink", [[filter.id]]);
                if (status(this) === "mounted") {
                    await this.loadFavorites();
                }
            },
        });
    },
});
