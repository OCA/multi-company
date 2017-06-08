# -*- coding: utf-8 -*-
# (c) 2015 Ainara Galdona - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class StockProductionLot(models.Model):

    _name = 'stock.production.lot'
    _inherit = ['multi.company.abstract', 'stock.production.lot']
    _description = 'Stock production lot for multi company'
