# Copyright 2017 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# Copyright 2018 Vicent Cubells - Tecnativa <vicent.cubells@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def taxes_by_company(self, field, company, match_tax_ids=None):
        taxes_ids = []
        if match_tax_ids is None:
            taxes_ids = company[field].ids
        # If None: return default taxes if []: return empty list
        if not match_tax_ids:
            return isinstance(taxes_ids, list) and taxes_ids or []
        AccountTax = self.env["account.tax"]
        taxes = AccountTax.browse(match_tax_ids)
        taxes_ids.extend(
            AccountTax.search(
                [("name", "in", taxes.mapped("name")), ("company_id", "=", company.id)]
            ).ids
        )
        return taxes_ids

    def set_multicompany_taxes(self):
        self.ensure_one()
        customer_tax_ids = self.taxes_id.ids
        supplier_tax_ids = self.supplier_taxes_id.ids
        company = self.env.company
        obj = self.sudo()
        default_customer_tax_ids = obj.taxes_by_company("account_sale_tax_id", company)
        default_supplier_tax_ids = obj.taxes_by_company(
            "account_purchase_tax_id", company
        )
        # Use list() to copy list
        match_customer_tax_ids = (
            default_customer_tax_ids != customer_tax_ids
            and list(customer_tax_ids)
            or None
        )
        match_suplier_tax_ids = (
            default_supplier_tax_ids != supplier_tax_ids
            and list(supplier_tax_ids)
            or None
        )
        for company in obj.env["res.company"].search([("id", "!=", company.id)]):
            customer_tax_ids.extend(
                obj.taxes_by_company(
                    "account_sale_tax_id", company, match_customer_tax_ids
                )
            )
            supplier_tax_ids.extend(
                obj.taxes_by_company(
                    "account_purchase_tax_id", company, match_suplier_tax_ids
                )
            )
        self.write(
            {
                "taxes_id": [(6, 0, customer_tax_ids)],
                "supplier_taxes_id": [(6, 0, supplier_tax_ids)],
            }
        )

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.set_multicompany_taxes()
        return res
