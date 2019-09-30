# -*- coding: utf-8 -*-
# Copyright 2019 AppsToGROW - Henrik Norlin
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from collections import defaultdict

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)

class IrRule(models.Model):
    _inherit = 'ir.rule'

    @api.model
    @tools.ormcache(
        'self.env.uid', 'self.env.user.company_id', 'model_name', 'mode')
    def _compute_domain(self, model_name, mode="read"):
        """ Let domain computation of security rules depend on company_id """
        _super = super(IrRule, self)._compute_domain
        model = self.env[model_name]
        if 'company_id' in model._fields:
            print model_name
            _super.clear_cache(self)
        return _super(model_name, mode=mode)
