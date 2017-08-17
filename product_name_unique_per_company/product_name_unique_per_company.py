# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
#    Copyright (C) 2016 Rossa S.A. (<http://www.rossa.com.py>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, _
from openerp.exceptions import Warning


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.one
    @api.constrains('company_id', 'name')
    def check_product_name_unique_per_company(self):
        if self.name and self.company_id:
            filters = [
                ('company_id', '=', self.company_id.id),
                ('name', '=ilike', self.name),
            ]
            product_ids = self.search(filters)
            if len(product_ids) > 1:
                raise Warning(
                    _("Product name must be unique for a company."))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
