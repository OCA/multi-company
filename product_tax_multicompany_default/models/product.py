# Copyright 2017 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# Copyright 2018 Vicent Cubells - Tecnativa <vicent.cubells@tecnativa.com>
# Copyright 2023 Eduardo de Miguel - Moduon <edu@moduon.team>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from typing import List

from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def taxes_by_company(self, field, company, match_tax_ids=None):
        taxes_ids = []
        if match_tax_ids is None:
            taxes_ids = company[field].ids
        # If None: return default taxes
        if not match_tax_ids:
            return taxes_ids
        AccountTax = self.env["account.tax"]
        for tax in AccountTax.browse(match_tax_ids):
            taxes_ids.extend(
                AccountTax.search(
                    [("name", "=", tax.name), ("company_id", "=", company.id)]
                ).ids
            )
        return taxes_ids

    def _delete_product_taxes(
        self,
        excl_customer_tax_ids: List[int] = None,
        excl_supplier_tax_ids: List[int] = None,
    ):
        """Delete taxes from product excluding chosen taxes

        :param excl_customer_tax_ids: Excluded customer tax ids
        :param excl_supplier_tax_ids: Excluded supplier tax ids
        """
        tax_where = " AND tax_id NOT IN %s"
        # Delete customer taxes
        customer_sql = "DELETE FROM product_taxes_rel WHERE prod_id IN %s"
        customer_sql_params = [tuple(self.ids)]
        if excl_customer_tax_ids:
            customer_sql += tax_where
            customer_sql_params.append(tuple(excl_customer_tax_ids))
        self.env.cr.execute(customer_sql + ";", customer_sql_params)
        # Delete supplier taxes
        supplier_sql = "DELETE FROM product_supplier_taxes_rel WHERE prod_id IN %s"
        supplier_sql_params = [tuple(self.ids)]
        if excl_supplier_tax_ids:
            supplier_sql += tax_where
            supplier_sql_params.append(tuple(excl_supplier_tax_ids))
        self.env.cr.execute(supplier_sql + ";", supplier_sql_params)

    def set_multicompany_taxes(self):
        self.ensure_one()
        user_company = self.env.company
        customer_tax = self.taxes_id
        customer_tax_ids = customer_tax.ids
        if not customer_tax.filtered(lambda r: r.company_id == user_company):
            customer_tax_ids = []
        supplier_tax = self.supplier_taxes_id
        supplier_tax_ids = supplier_tax.ids
        if not supplier_tax.filtered(lambda r: r.company_id == user_company):
            supplier_tax_ids = []
        obj = self.sudo()
        default_customer_tax_ids = obj.taxes_by_company(
            "account_sale_tax_id", user_company
        )
        default_supplier_tax_ids = obj.taxes_by_company(
            "account_purchase_tax_id", user_company
        )
        # Clean taxes from other companies (cannot replace it with sudo)
        self._delete_product_taxes(
            excl_customer_tax_ids=customer_tax_ids,
            excl_supplier_tax_ids=supplier_tax_ids,
        )
        # Use list() to copy list
        match_customer_tax_ids = (
            list(customer_tax_ids)
            if default_customer_tax_ids != customer_tax_ids
            else None
        )
        match_suplier_tax_ids = (
            list(supplier_tax_ids)
            if default_supplier_tax_ids != supplier_tax_ids
            else None
        )
        for company in obj.env["res.company"].search([("id", "!=", user_company.id)]):
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

    @api.model_create_multi
    def create(self, vals_list):
        new_products = super().create(vals_list)
        for product in new_products:
            product.set_multicompany_taxes()
        return new_products


class ProductProduct(models.Model):
    _inherit = "product.product"

    def set_multicompany_taxes(self):
        self.product_tmpl_id.set_multicompany_taxes()
