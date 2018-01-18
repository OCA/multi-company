# -*- coding: utf-8 -*-
# Copyright 2016 Lorenzo Battistini - Agile Business Group
# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class SaleLayoutCategory(models.Model):
    _inherit = ['multi.company.abstract', 'sale.layout_category']
    _name = 'sale.layout_category'
