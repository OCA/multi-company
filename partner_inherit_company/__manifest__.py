#  Copyright 2023 Simone Rubino - Aion Tech
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Partner inherit company",
    "summary": "Access partners of parent, children and siblings companies.",
    "author": "Aion Tech, Odoo Community Association (OCA)",
    "maintainers": [
        "SirAionTech",
    ],
    "website": "https://github.com/OCA/multi-company"
    "/tree/16.0/partner_inherit_company",
    "category": "Partner Management",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "base_inherit_company",
        "partner_multi_company",
    ],
    "post_init_hook": "post_init_hook",
}
