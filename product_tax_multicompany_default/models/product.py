# Copyright 2017 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# Copyright 2018 Vicent Cubells - Tecnativa <vicent.cubells@tecnativa.com>
# Copyright 2023 Eduardo de Miguel - Moduon <edu@moduon.team>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    divergent_company_taxes = fields.Boolean(
        string="Has divergent cross-company taxes",
        compute="_compute_divergent_company_taxes",
        compute_sudo=True,
        help=(
            "Does this product have divergent cross-company taxes? "
            "(Only for multi-company products)"
        ),
    )

    @api.depends("company_id", "taxes_id", "supplier_taxes_id")
    def _compute_divergent_company_taxes(self):
        """Know if this product has divergent taxes across companies."""
        # Skip single-company products
        self.divergent_company_taxes = False
        if len(self.env["res.company"].search([]).ids) == 1:
            return
        for one in self:
            # A unique constraint in account.tax makes it impossible to have
            # duplicated tax names by company
            if self.company_id:
                continue
            one.divergent_company_taxes = one._is_divergent_company_taxes(
                "taxes"
            ) or self._is_divergent_company_taxes("purchase")

    def _is_divergent_company_taxes(self, tax_type):
        """Returns true or false if there are differences in product taxes.

        :param tax_type: can be 'taxes' or 'purchase'
        """
        self.ensure_one()
        all_companies = self.env["res.company"].search(
            [
                # Useful for tests, to avoid pollution
                ("id", "not in", self.env.context.get("ignored_company_ids", [])),
            ]
        )
        current_company = self.env.company

        company_tax_bd_map = dict(self._origin._get_product_taxes(tax_type))
        for company_id in list(company_tax_bd_map.keys()):
            if company_id not in all_companies.ids or company_id == current_company.id:
                company_tax_bd_map.pop(company_id)
        if tax_type == "taxes":
            current_tax = self.taxes_id
            field_name_data = "account_sale_tax_id"
        elif tax_type == "purchase":
            current_tax = self.supplier_taxes_id
            field_name_data = "account_purchase_tax_id"
        propagate_taxes = False

        # Tax-free
        if not current_tax:
            # Since all companies can have an empty tax field,if there is data
            # in the database, it means that we can propagate leaving it empty.
            if len(company_tax_bd_map) > 0:
                propagate_taxes = True
        # No tax in other products
        elif not company_tax_bd_map:
            # If we do not have any taxes in the database and we add a tax, it means
            # that we can update the product taxes.
            current_product_tax_ids = current_tax.filtered(
                lambda tax: tax.company_id == current_company
            ).ids
            current_product_taxes_other_companies = set()
            other_companies = all_companies.filtered(
                lambda company: company.id != current_company.id
            )
            for company in other_companies:
                current_product_taxes_other_companies.update(
                    self._taxes_by_company(
                        field_name_data, company, current_product_tax_ids
                    )
                )
            if len(current_product_taxes_other_companies) > 0:
                propagate_taxes = True
        else:
            current_names = current_tax.filtered(
                lambda tax: tax.company_id == current_company
            ).mapped("name")
            current_product_tax_ids = current_tax.filtered(
                lambda tax: tax.company_id == current_company
            ).ids
            for company in all_companies - current_company:
                if company_tax_bd_map.get(company.id) and current_names == list(
                    company_tax_bd_map.get(company.id).values()
                ):
                    continue
                # We are looking to see if there are any taxes that can be applied to
                # other companies from the taxes that the current product has.
                current_product_taxes_other_companies = self._taxes_by_company(
                    field_name_data,
                    self.env["res.company"].browse(company.id),
                    current_product_tax_ids,
                )
                if len(current_product_taxes_other_companies) == len(current_tax):
                    propagate_taxes = True
                    break

        return propagate_taxes

    def _get_product_taxes(self, field):
        """Returns taxes on purchase or sales taxes

        We need the product taxes for other companies, and we cannot take
        them from the object itself, so we have to consult the database
        where the product taxes passed by parameter are located for all
        companies.

        :param field: can be 'taxes' or 'purchase'
        """
        if not self.ids:
            return []
        # Need stay her because sometimes can be empty
        self.ensure_one()

        table_by_field = {
            "taxes": "product_taxes_rel",
            "purchase": "product_supplier_taxes_rel",
        }
        field_name = table_by_field.get(field)

        if not field_name:
            raise ValueError("field should be 'taxes' or 'purchase'")

        sql = f"""
            SELECT DISTINCT a_tax.company_id, a_tax.name
            FROM {field_name} ptr
            LEFT JOIN account_tax a_tax ON tax_id = a_tax.id
            WHERE ptr.prod_id = %s
            """
        self.env.cr.execute(sql, [self.id])
        return self.env.cr.fetchall()

    def _taxes_by_company(self, field, company, match_tax_ids=None):
        """Returns the IDs of all accounts that match the parameters passed.

        :param field: fields to search (account_sale_tax_id or account_purchase_tax_id)
        :param company: company to search for
        :param match_tax_ids: tax IDs to search for
        """
        taxes_ids = []
        if match_tax_ids is None:
            taxes_ids = company[field].ids
        # If None: return default taxes
        if not match_tax_ids:
            return taxes_ids
        type_tax_use = "sale" if field == "account_sale_tax_id" else "purchase"
        account_tax = self.env["account.tax"].sudo().browse(match_tax_ids)
        taxes = account_tax.filtered_domain([("type_tax_use", "=", type_tax_use)])
        if not taxes:
            return []
        return account_tax.search(
            [
                ("type_tax_use", "=", type_tax_use),
                ("company_id", "=", company.id),
                ("name", "in", taxes.mapped("name")),
            ]
        ).ids

    def _delete_product_taxes(
        self,
        excl_customer_tax_ids: list[int] = None,
        excl_supplier_tax_ids: list[int] = None,
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
        self.env.cr.execute(customer_sql, customer_sql_params)
        # Delete supplier taxes
        supplier_sql = "DELETE FROM product_supplier_taxes_rel WHERE prod_id IN %s"
        supplier_sql_params = [tuple(self.ids)]
        if excl_supplier_tax_ids:
            supplier_sql += tax_where
            supplier_sql_params.append(tuple(excl_supplier_tax_ids))
        self.env.cr.execute(supplier_sql, supplier_sql_params)

    def set_multicompany_taxes(self):
        self.ensure_one()
        user_company = self.env.company
        customer_tax = self.taxes_id
        customer_tax_ids = customer_tax.ids
        if not customer_tax.filtered(lambda tax: tax.company_id == user_company):
            customer_tax_ids = []
        supplier_tax = self.supplier_taxes_id
        supplier_tax_ids = supplier_tax.ids
        if not supplier_tax.filtered(lambda tax: tax.company_id == user_company):
            supplier_tax_ids = []
        default_customer_tax_ids = self._taxes_by_company(
            "account_sale_tax_id", user_company
        )
        default_supplier_tax_ids = self._taxes_by_company(
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
        for company in self.env["res.company"].search([("id", "!=", user_company.id)]):
            customer_tax_ids.extend(
                self._taxes_by_company(
                    "account_sale_tax_id", company, match_customer_tax_ids
                )
            )
            supplier_tax_ids.extend(
                self._taxes_by_company(
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
        new_products.invalidate_recordset(fnames=["taxes_id", "supplier_taxes_id"])
        return new_products


class ProductProduct(models.Model):
    _inherit = "product.product"

    def set_multicompany_taxes(self):
        self.product_tmpl_id.set_multicompany_taxes()
