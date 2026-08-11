# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Mail Multicompany Switch Notify",
    "version": "18.0.1.0.0",
    "category": "Extra Tools",
    "summary": "Warn the user when switching to a company with no outgoing "
    "mail server configured",
    "author": "Muhammad Haroon Khan, Odoo Community Association (OCA)",
    "maintainers": ["mharoonkhan123"],
    "website": "https://github.com/OCA/multi-company",
    "development_status": "Beta",
    "license": "AGPL-3",
    "depends": ["mail_multicompany", "web"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "mail_multicompany_switch_notify/static/src/js/switch_company_mail_check.js",
            "mail_multicompany_switch_notify/static/src/js/mail_server_company_check.js",
            "mail_multicompany_switch_notify/static/src/xml/mail_server_company_check.xml",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}
