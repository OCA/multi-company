# -*- coding: utf-8 -*-
# Copyright 2017 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def taxes_by_company(self, field, company_id):
        taxes_ids = self.sudo().env['ir.values'].get_default(
            'product.template', field, company_id=company_id)
        return isinstance(taxes_ids, list) and taxes_ids or []

    @api.multi
    def set_multicompany_taxes(self):
        self.ensure_one()
        customer_tax_ids = self.taxes_id.ids
        supplier_tax_ids = self.supplier_taxes_id.ids
        if not customer_tax_ids:
            customer_tax_ids = self.taxes_by_company(
                'taxes_id', self.env.user.company_id.id)
        if not supplier_tax_ids:
            supplier_tax_ids = self.taxes_by_company(
                'taxes_id', self.env.user.company_id.id)
        for company in self.sudo().env['res.company'].search([
            ('id', '!=', self.env.user.company_id.id)
        ]):
            default_customer_tax_ids = self.taxes_by_company(
                'taxes_id', company.id)
            default_supplier_tax_ids = self.taxes_by_company(
                'supplier_taxes_id', company.id)
            if default_customer_tax_ids not in customer_tax_ids:
                customer_tax_ids.extend(default_customer_tax_ids)
            if default_supplier_tax_ids not in supplier_tax_ids:
                supplier_tax_ids.extend(default_supplier_tax_ids)
        self.write({
            'taxes_id': [(6, 0, customer_tax_ids)],
            'supplier_taxes_id': [(6, 0, supplier_tax_ids)],
        })

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        res.set_multicompany_taxes()
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def set_multicompany_taxes(self):
        self.product_tmpl_id.set_multicompany_taxes()
