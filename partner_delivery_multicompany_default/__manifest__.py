# Copyright 2023 Moduon Team S.L.
# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Partner Delivery Multi-Company Default",
    "summary": "Set a default delivery carrier for all companies of a partners",
    "version": "16.0.0.1.0",
    "development_status": "Alpha",
    "category": "Inventory/Delivery",
    "website": "https://github.com/OCA/multi-company",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["camptocamp"],
    "license": "LGPL-3",
    "depends": [
        "partner_base_multicompany_default",
        "delivery",
    ],
    "data": [
        "views/partner_view.xml",
    ],
}
