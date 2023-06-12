# Copyright 2018 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Quick Company Creation Wizard",
    "summary": "This module adds a wizard to create companies easily",
    "version": "16.0.1.0.0",
    "category": "Multicompany",
    "website": "https://github.com/OCA/multi-company",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["account"],
    "data": ["wizards/multicompany_easy_creation.xml", "security/ir.model.access.csv"],
}
