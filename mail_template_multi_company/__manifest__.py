# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Mail Template Multi Company",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": ["mail"],
    "post_init_hook": "post_init_hook",
    "data": ["security/mail_template.xml", "views/mail_template.xml"],
    "development_status": "Beta",
    "maintainers": ["Olivier-LAURENT"],
}
