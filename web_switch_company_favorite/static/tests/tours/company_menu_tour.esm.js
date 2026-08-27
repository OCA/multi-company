import {registry} from "@web/core/registry";

// Tour 1: Apply filter
registry.category("web_tour.tours").add("web_switch_company_favorite_apply", {
    url: "/web",
    steps: () => [
        {
            content: "Open switch company menu",
            trigger: ".o_switch_company_menu button",
            run: "click",
        },
        {
            content: "Click on Favorites tab",
            trigger: ".o_company_tab_favorites",
            run: "click",
        },
        {
            content: "Verify that the user favorite filter is listed first",
            trigger: ".o_favorite_filter_item:eq(0) span:contains('Filter C and D')",
        },
        {
            content: "Verify that the divider exists before shared filters",
            trigger: ".o_company_favorites_list .dropdown-divider",
        },
        {
            content: "Verify that the shared filter is listed second",
            trigger: ".o_favorite_filter_item:eq(1) span:contains('Filter A and B')",
        },
        {
            content: "Click on Filter C and D",
            trigger: ".o_favorite_filter_item span:contains('Filter C and D')",
            run: "click",
        },
        {
            content: "Verify active tab changed back to Companies",
            trigger: ".o_company_tab_companies.active",
        },
        {
            content: "Verify Company C is selected",
            trigger:
                ".o_switch_company_item:has(.company_label:contains('Company C')) [role='menuitemcheckbox'][aria-checked='true']",
        },
        {
            content: "Verify Company D is selected",
            trigger:
                ".o_switch_company_item:has(.company_label:contains('Company D')) [role='menuitemcheckbox'][aria-checked='true']",
        },
        {
            content: "Verify Confirm button is visible",
            trigger:
                ".o_switch_company_menu_buttons button.btn-primary:contains('Confirm')",
        },
    ],
});

// Tour 2: Create filter
registry.category("web_tour.tours").add("web_switch_company_favorite_create", {
    url: "/web",
    steps: () => [
        {
            content: "Open switch company menu",
            trigger: ".o_switch_company_menu button",
            run: "click",
        },
        {
            content: "Click on Favorites tab",
            trigger: ".o_company_tab_favorites",
            run: "click",
        },
        {
            content: "Click Create button",
            trigger: ".o_company_menu_wrapper button:contains('Create')",
            run: "click",
        },
        {
            content: "Wait for form dialog and type filter name",
            trigger: ".modal input#name_0, .modal [name='name'] input",
            run: "edit New Filter Created",
        },
        {
            content: "Save new filter",
            trigger:
                ".modal-footer button.o_form_button_save, .modal-footer button.btn-primary, .modal-footer button:contains('Save')",
            run: "click",
        },
        {
            content: "Wait for create dialog to close",
            trigger: "body:not(:has(.modal)):not(:has(.modal-backdrop))",
        },
        {
            content: "Verify new filter exists",
            trigger: ".o_favorite_filter_item span:contains('New Filter Created')",
        },
    ],
});

// Tour 3: Edit filter
registry.category("web_tour.tours").add("web_switch_company_favorite_edit", {
    url: "/web",
    steps: () => [
        {
            content: "Open switch company menu",
            trigger: ".o_switch_company_menu button",
            run: "click",
        },
        {
            content: "Click on Favorites tab",
            trigger: ".o_company_tab_favorites",
            run: "click",
        },
        {
            content: "Click Edit button on filter to edit",
            trigger:
                ".o_favorite_filter_item:has(span:contains('Filter To Edit')) button[title='Edit filter']",
            run: "click",
        },
        {
            content: "Type Demo User in Shared with field",
            trigger: ".modal div[name='user_ids'] input, .modal input#user_ids_0",
            run: "edit Demo User",
        },
        {
            content: "Select Demo User from dropdown",
            trigger:
                ".o-autocomplete--dropdown-item:contains('Demo User'), .ui-menu-item a:contains('Demo User')",
            run: "click",
        },
        {
            content: "Modify filter name in edit dialog",
            trigger: ".modal input#name_0, .modal [name='name'] input",
            run: "edit Filter To Edit Edited",
        },
        {
            content: "Save edited filter",
            trigger:
                ".modal-footer button.o_form_button_save, .modal-footer button.btn-primary, .modal-footer button:contains('Save')",
            run: "click",
        },
        {
            content: "Wait for edit dialog to close",
            trigger: "body:not(:has(.modal)):not(:has(.modal-backdrop))",
        },
        {
            content: "Verify edited filter exists",
            trigger: ".o_favorite_filter_item span:contains('Filter To Edit Edited')",
        },
    ],
});

// Tour 4: Delete filter
registry.category("web_tour.tours").add("web_switch_company_favorite_delete", {
    url: "/web",
    steps: () => [
        {
            content: "Open switch company menu",
            trigger: ".o_switch_company_menu button",
            run: "click",
        },
        {
            content: "Click on Favorites tab",
            trigger: ".o_company_tab_favorites",
            run: "click",
        },
        {
            content: "Click Delete button on filter to delete",
            trigger:
                ".o_favorite_filter_item:has(span:contains('Filter To Delete')) button[title='Delete filter']",
            run: "click",
        },
        {
            content: "Confirm delete in dialog",
            trigger:
                ".modal-footer button.btn-primary:contains('Ok'), .modal-footer button.btn-primary:contains('Confirm'), .modal-footer button.btn-primary",
            run: "click",
        },
        {
            content: "Wait for delete dialog to close",
            trigger: "body:not(:has(.modal)):not(:has(.modal-backdrop))",
        },
        {
            content: "Verify filter was deleted",
            trigger: ".o_company_favorites_list:not(:contains('Filter To Delete'))",
        },
    ],
});
