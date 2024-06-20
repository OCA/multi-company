# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Partner Account Payment Mode Multi-Company Default",
    "summary": "Set a default payment mode for all companies of a partners",
    "version": "16.0.0.1.0",
    "development_status": "Alpha",
    "category": "Banking addons",
    "website": "https://github.com/OCA/multi-company",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["camptocamp"],
    "license": "LGPL-3",
    "depends": [
        "partner_base_multicompany_default",
        "account_payment_partner",
    ],
    "data": [
        "views/partner_view.xml",
    ],
}
