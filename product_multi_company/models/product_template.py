# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License LGPL-3.0 - http://www.gnu.org/licenses/lgpl.html

from odoo import models


class ProductTemplate(models.Model):
    _inherit = ["multi.company.abstract", "product.template"]
    _name = "product.template"
