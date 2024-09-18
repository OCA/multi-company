# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Mass Mailing Multi Company",
    "summary": "Adds the company_id field to the models mailing.mailing,"
    " mailing.list and mailing.contact",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": ["mass_mailing"],
    "data": [
        "security/mass_mailing.xml",
        "views/mailing_mailing_views.xml",
        "views/mailing_list_views.xml",
        "views/mailing_contact_views.xml",
    ],
}
