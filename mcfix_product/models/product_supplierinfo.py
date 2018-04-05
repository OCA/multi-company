# -*- coding: utf-8 -*-
# Copyright 2017 Creu Blanca.
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models, _
from odoo.exceptions import ValidationError


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.constrains('company_id', 'product_id')
    def _check_company_product(self):
        if self.product_id.company_id and self.product_id.company_id != \
                self.company_id:
            raise ValidationError(_(
                'Company %s defined in the product does not match '
                'with that defined in the supplier info record %s') % (
                    self.product_id.name, self.name))

    @api.constrains('company_id', 'name')
    def _check_company_partner(self):
        if self.name.company_id and self.name.company_id != \
                self.company_id:
            raise ValidationError(_(
                'Company %s defined in the supplier does not match '
                'with that defined in the supplier info record.') %
                self.product_id.name)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.name.company_id and self.name.company_id != self.company_id:
            self.name = False
        if self.product_id.company_id and self.product_id.company_id != \
                self.company_id:
            self.product_id = False
