# -*- coding: utf-8 -*-
# Copyright 2017 Creu Blanca.
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def _compute_current_company_id(self):
        for pt in self:
            pt.current_company_id = self.env['res.company'].browse(
                pt._context.get('force_company') or
                pt.env.user.company_id.id).ensure_one()

    current_company_id = fields.Many2one(
        comodel_name='res.company',
        default=_compute_current_company_id,
        compute='_compute_current_company_id',
        store=False
    )

    @api.constrains('company_id', 'seller_ids')
    def _check_company_seller(self):
        for seller in self.seller_ids:
            if self.company_id and seller.company_id != self.company_id:
                raise ValidationError(_(
                    'Company %s defined in the product does not match '
                    'with that defined in the supplier info record %s') % (
                        self.company_id.name, seller.name))
