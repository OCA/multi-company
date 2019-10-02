# -*- coding: utf-8 -*-
# Copyright 2019 Sunflower IT
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models, SUPERUSER_ID
from odoo.http import request

_logger = logging.getLogger(__name__)


def invalidate_cache_for_user(env, uid):
    for this in list(env.all):
        if not this.uid == uid:
            continue
        this.cache.clear()
        this._protected.clear()
        this.dirty.clear()


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _dispatch(cls):
        """ Clear cache when a user switches to another domain name """
        uid = request.session.get('uid')
        domain_name = request.httprequest.host.partition(":")[0]
        cached_domain_name = request.registry['res.users']\
            .get_cached_domain_name(uid, domain_name)
        # Dont trigger on longpolling because this occurs too often
        if uid and uid != SUPERUSER_ID and \
                domain_name != cached_domain_name and \
                'longpolling' not in request.httprequest.path:
            _logger.info(
                "Clearing cache after seeing user %s access Odoo through "
                "domain name %s instead of %s",
                uid, cached_domain_name, domain_name)
            request.registry.clear_caches()
            invalidate_cache_for_user(request.env, uid)
        return super(IrHttp, cls)._dispatch()
