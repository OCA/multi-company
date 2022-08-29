#  Copyright (c) Akretion 2021
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Purchase Quick Intercompany",
    "version": "14.0.0.1.1",
    "category": "Purchase",
    "author": "Odoo Community Association (OCA), " "Akretion",
    "website": "https://github.com/OCA/multi-company",
    "license": "AGPL-3",
    "data": ["views/product_view.xml", "views/product_template_view.xml"],
    "depends": [
        "purchase_quick",
        "purchase_sale_inter_company",
        "intercompany_shared_contact",
    ],
    "installable": True,
}
