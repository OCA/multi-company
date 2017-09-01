# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, SUPERUSER_ID


def pre_init_hook(cr):

    with api.Environment.manage():

        env = api.Environment(cr, SUPERUSER_ID, {})
        websites = env['website'].search([])

        if len(websites) <= 1:
            return

        public_user = env.ref('base.public_user')
        used_existing = False

        for website in websites:

            if all((
                website.company_id == public_user.company_id,
                website.user_id == public_user,
                not used_existing,
            )):
                used_existing = True
                continue

            user = public_user.copy()
            user.company_id = website.company_id.id
            website.user_id = user.id
