# Copyright 2017 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# Copyright 2018 Vicent Cubells - Tecnativa <vicent.cubells@tecnativa.com>
# Copyright 2023 Eduardo de Miguel - Moduon <edu@moduon.team>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from typing import List

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    divergent_company_taxes = fields.Boolean(
        string="Has divergent cross-company taxes",
        compute="_compute_divergent_company_taxes",
        compute_sudo=True,
        store=True,
        help=(
            "Does this product have divergent cross-company taxes? "
            "(Only for multi-company products)"
        ),
    )

    @api.depends("company_id", "taxes_id", "supplier_taxes_id")
    def _compute_divergent_company_taxes(self):
        """Know if this product has divergent taxes across companies."""
        all_companies = self.env["res.company"].search(
            [
                # Useful for tests, to avoid pollution
                ("id", "not in", self.env.context.get("ignored_company_ids", []))
            ]
        )
        for one in self:
            one.divergent_company_taxes = False
            # Skip single-company products
            if one.company_id:
                continue
            # A unique constraint in account.tax makes it impossible to have
            # duplicated tax names by company
            if self.user_has_groups("product_tax_multicompany_default.tax_man_mapping"):
                one.divergent_company_taxes = bool(
                    self._get_group_divergent_taxes(one.taxes_id)
                    or self._get_group_divergent_taxes(one.supplier_taxes_id)
                )
            else:
                customer_taxes = {
                    frozenset(
                        tax.name for tax in one.taxes_id if tax.company_id == company
                    )
                    for company in all_companies
                }
                if len(customer_taxes) > 1:
                    one.divergent_company_taxes = True
                    continue
                supplier_taxes = {
                    frozenset(
                        tax.name
                        for tax in one.supplier_taxes_id
                        if tax.company_id == company
                    )
                    for company in all_companies
                }
                if len(supplier_taxes) > 1:
                    one.divergent_company_taxes = True
                    continue

    @api.model
    def _get_group_divergent_taxes(self, product_tax_ids):
        tax_map_ids = product_tax_ids.mapped("company_map_id")
        if len(tax_map_ids) == 1:
            tax_ids = self.env["account.tax"].search(
                [
                    ("company_map_id", "=", tax_map_ids.id),
                    ("type_tax_use", "in", product_tax_ids.mapped("type_tax_use")),
                ],
            )
            return tax_ids - product_tax_ids
        return False

    def taxes_by_company(self, field, company, match_tax_ids=None):
        taxes_ids = []
        if match_tax_ids is None:
            taxes_ids = company[field].ids
        # If None: return default taxes
        if not match_tax_ids:
            return taxes_ids
        AccountTax = self.env["account.tax"]
        for tax in AccountTax.browse(match_tax_ids):
            if self.user_has_groups("product_tax_multicompany_default.tax_man_mapping"):
                taxes_ids.extend(
                    AccountTax.search(
                        [
                            ("company_map_id", "=", tax.company_map_id.id),
                            ("company_id", "=", company.id),
                            ("type_tax_use", "=", tax.type_tax_use),
                        ],
                        limit=1,
                    ).ids
                )
            else:
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

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.set_multicompany_taxes()
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"

    def set_multicompany_taxes(self):
        self.product_tmpl_id.set_multicompany_taxes()
