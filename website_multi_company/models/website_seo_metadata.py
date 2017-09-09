# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models


class WebsiteSeoMetadata(models.AbstractModel):
    _inherit = ['multi.company.abstract', 'website.seo.metadata']
    _name = 'website.seo.metadata'
