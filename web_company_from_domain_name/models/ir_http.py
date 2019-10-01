# -*- coding: utf-8 -*-
# Copyright 2019 Sunflower IT
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _dispatch(cls):
        """ Clear cache when a user switches to another domain name """
        uid = request.session.uid
        domain_name = request.httprequest.host.partition(":")[0]
        cached_domain_name = request.registry['res.users']\
            .get_cached_domain_name(uid, domain_name)
        # Dont trigger on longpolling because this occurs too often
        if domain_name != cached_domain_name and not \
                'longpolling' in request.httprequest.path:
            _logger.info(
                "Clearing cache after seeing user %s access Odoo through "
                "domain name %s instead of %s",
                uid, cached_domain_name, domain_name)
            request.registry.clear_caches()
            # TODO: only invalidate envs for this user, not all
            request.env.invalidate_all()
            request.env['res.users'].get_cached_company_id(uid)
        return super(IrHttp, cls)._dispatch()
