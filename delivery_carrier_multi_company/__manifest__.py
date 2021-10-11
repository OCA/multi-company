# Copyright 2021 Acsone SA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Delivery Carrier multi-company",
    "summary": "Select individually the delivery-carrier visibility on each " "company",
    "author": "Tecnativa," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "category": "Delivery",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base_multi_company", "delivery", "product_multi_company"],
    "data": ["views/delivery_carrier.xml"],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
