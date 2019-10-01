# -*- coding: utf-8 -*-
# Copyright 2019 AppsToGROW - Henrik Norlin
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models

import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    access_url = fields.Char(
        string="Access domain name",
        help="If filled, accessing Odoo through this "
             "domain name will select this company as the "
             "current one for that session.")
