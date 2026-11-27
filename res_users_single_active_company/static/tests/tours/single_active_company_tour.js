odoo.define("res_users_single_active_company.tour", function (require) {
    "use strict";

    const tour = require("web_tour.tour");

    tour.register(
        "res_users_single_active_company.single_active_company",
        {
            test: true,
            rainbowMan: false,
        },
        [
            {
                content: "The warning dialog is visible",
                trigger: ".o_single_active_company_dialog",
                run() {
                    // This step checks that the element is visible.
                },
            },
            {
                content: "Escape does not close the dialog",
                trigger: ".o_single_active_company_dialog",
                run() {
                    window.dispatchEvent(
                        new KeyboardEvent("keydown", {
                            key: "Escape",
                            code: "Escape",
                            bubbles: true,
                        })
                    );
                },
            },
            {
                content: "The dialog stays open",
                trigger: ".o_single_active_company_dialog",
                run() {
                    // This step checks that the element is visible.
                },
            },
            {
                content: "The current company is preselected",
                trigger:
                    ".o_single_active_company_dialog .o_single_active_company_item .fa-check-square",
                run() {
                    // This step checks that the element is visible.
                },
            },
            {
                content: "Select company A",
                trigger:
                    ".o_single_active_company_dialog .company_label:contains(Single Active A)",
                run: "click",
            },
            {
                content: "Confirm the selected company",
                trigger: "button.o_single_active_company_confirm:not(:disabled)",
                run: "click",
            },
            {
                content: "The systray shows company A",
                trigger:
                    ".o_switch_company_menu .oe_topbar_name:contains(Single Active A)",
                run() {
                    // This step checks that the element is visible.
                },
            },
            {
                content: "Open the company menu",
                trigger: ".o_switch_company_menu .dropdown-toggle",
                run: "click",
            },
            {
                content: "Select company B",
                trigger:
                    ".o_switch_company_menu .company_label:contains(Single Active B)",
                run: "click",
            },
            {
                content: "The systray shows company B",
                trigger:
                    ".o_switch_company_menu .oe_topbar_name:contains(Single Active B)",
                run() {
                    // This step checks that the element is visible.
                },
            },
            {
                content: "Open the company menu again",
                trigger: ".o_switch_company_menu .dropdown-toggle",
                run: "click",
            },
            {
                content: "The menu shows one checked company",
                trigger: ".o_switch_company_menu .fa-check-square",
                run() {
                    const checks = document.querySelectorAll(
                        ".o_switch_company_menu .fa-check-square"
                    );
                    if (checks.length !== 1) {
                        throw new Error("The menu must show one checked company.");
                    }
                },
            },
        ]
    );
});
