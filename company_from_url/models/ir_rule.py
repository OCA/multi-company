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

    ''' COMPUTE DOMAIN PER COMPANY'''

    # /base/ir/ir_rule.py
    # This did not work:
    # @api.model
    # @tools.ormcache('self.env.uid', 'self.env.user.company_id', 'model_name', 'mode') #UPDATED
    # def _compute_domain(self, model_name, mode="read"):
    #     return super(IrRule, self)._compute_domain(model_name, mode=mode)


    # https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/ir/ir_rule.py
    # - @tools.ormcache('self._uid', 'model_name', 'mode')
    # + @tools.ormcache('self.env.uid', 'self.env.context.get("company_id")', 'model_name', 'mode')
    @api.model
    @tools.ormcache('self.env.uid', 'self.env.user.company_id', 'model_name', 'mode')
    def _compute_domain(self, model_name, mode="read"):
        if mode not in self._MODES:
            raise ValueError('Invalid mode: %r' % (mode,))

        if self._uid == SUPERUSER_ID:
            return None

        query = """ SELECT r.id FROM ir_rule r JOIN ir_model m ON (r.model_id=m.id)
                    WHERE m.model=%s AND r.active AND r.perm_{mode}
                    AND (r.id IN (SELECT rule_group_id FROM rule_group_rel rg
                                  JOIN res_groups_users_rel gu ON (rg.group_id=gu.gid)
                                  WHERE gu.uid=%s)
                         OR r.global)
                """.format(mode=mode)
        self._cr.execute(query, (model_name, self._uid))
        rule_ids = [row[0] for row in self._cr.fetchall()]
        if not rule_ids:
            return []

        # read 'domain' as self._uid to have the correct eval context for the rules.
        rules = self.browse(rule_ids)
        rule_domain = {vals['id']: vals['domain'] for vals in rules.read(['domain'])}

        # browse user and rules as SUPERUSER_ID to avoid access errors!
        user = self.env.user
        global_domains = []                     # list of domains
        group_domains = defaultdict(list)       # {group: list of domains}
        for rule in rules.sudo():
            dom = expression.normalize_domain(rule_domain[rule.id])
            if rule.groups & user.groups_id:
                group_domains[rule.groups[0]].append(dom)
            if not rule.groups:
                global_domains.append(dom)

        # combine global domains and group domains
        if group_domains:
            group_domain = expression.OR(map(expression.OR, group_domains.values()))
        else:
            group_domain = []
        domain = expression.AND(global_domains + [group_domain])
        return domain
