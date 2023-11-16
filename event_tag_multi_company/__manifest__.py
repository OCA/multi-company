{
    "name": "Event tag multi company",
    "summary": "This module is useful to handle event tags in a multi "
    "company environment",
    "author": "Le Filament, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["event"],
    "data": [
        "security/event_tag_security.xml",
        # datas
        # views
        "views/event_tag_views.xml",
        # views menu
        # wizard
    ],
    "assets": {
        "web._assets_primary_variables": [],
        "web._assets_frontend_helpers": [],
        "web.assets_frontend": [],
        "web.assets_tests": [],
        "web.assets_qweb": [],
    },
    "installable": True,
    "auto_install": False,
}
