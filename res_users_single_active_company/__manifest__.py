# Copyright 2026 XXP LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Users Single Active Company",
    "summary": "Limit a user to one active company when Single Active Company "
    "is enabled",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "license": "AGPL-3",
    "author": "XXP LLC, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": ["web", "web_tour"],
    "pre_init_hook": "pre_init_hook",
    "data": [
        "views/res_users_views.xml",
    ],
    "demo": [
        "demo/res_company.xml",
        "demo/res_users.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "res_users_single_active_company/static/src/js/company_service.esm.js",
            "res_users_single_active_company/static/src/js/switch_company_menu.esm.js",
            "res_users_single_active_company/static/src/js/single_active_company_dialog.esm.js",
            "res_users_single_active_company/static/src/xml/switch_company_menu.xml",
            "res_users_single_active_company/static/src/xml/single_active_company_dialog.xml",
        ],
        "web.assets_tests": [
            "res_users_single_active_company/static/tests/tours/single_active_company_tour.js",
        ],
    },
}
