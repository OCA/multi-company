# Copyright 2026 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
# @author Pierre Verkest <pierre@verkest.fr>

{
    "name": "Web Switch Company Favorite",
    "summary": "Add favorites tab to company switcher menu",
    "version": "19.0.1.0.0",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "maintainers": ["petrus-v"],
    "depends": [
        # Odoo Community
        "web",
    ],
    "data": [],
    "demo": [],
    "assets": {
        "web.assets_backend": [
            "web_switch_company_favorite/static/src/js/**/*",
            "web_switch_company_favorite/static/src/xml/**/*",
            "web_switch_company_favorite/static/src/scss/**/*",
        ],
        "web.assets_tests": [
            "web_switch_company_favorite/static/tests/tours/**/*",
        ],
    },
    "installable": True,
}
