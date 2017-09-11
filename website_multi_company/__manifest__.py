# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Website - Multi-Company",
    "summary": "This module isolates websites by company.",
    "version": "10.0.1.0.0",
    "category": "Website",
    "website": "https://laslabs.com/",
    "author": "LasLabs, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "installable": True,
    "post_init_hook": "post_init_hook",
    "depends": [
        'auth_signup',
        'website',
    ],
}
