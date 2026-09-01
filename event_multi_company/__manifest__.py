# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Event multi-company",
    "summary": "Assign an event to several companies (backend only).",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "INVITU, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "category": "Marketing",
    "depends": [
        "base_multi_company",
        "event",
    ],
    "data": [
        "views/event_event_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
