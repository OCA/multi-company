# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Login All Company",
    "summary": """
        Access all your companies when you log in""",
    "version": "15.0.0.0.0",
    "license": "AGPL-3",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": ["web"],
    "assets": {
        "web.assets_backend": [
            "login_all_company/static/src/js/*.js",
        ],
    },
}
