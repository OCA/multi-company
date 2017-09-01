# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):

    def _get_search_domain(self, *args, **kwargs):
        domain = super(WebsiteSale, self)._get_search_domain(*args, **kwargs)
        domain += ('company_id', '=', request.website.company_id.id)
        return domain
