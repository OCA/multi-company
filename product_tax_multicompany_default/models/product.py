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

    def _get_tax_source_company(self):
        """Company whose taxes are propagated to the other companies.

        A branch uses the taxes of its parent company and usually has none of
        its own, so the first company of the hierarchy owning taxes is used.
        """
        company = self.env.company
        tax_model = self.env["account.tax"].sudo().with_context(active_test=False)
        while company.parent_id and not tax_model.search_count(
            [("company_id", "=", company.id)], limit=1
        ):
            company = company.parent_id
        return company

    @api.depends("company_id", "taxes_id", "supplier_taxes_id")
    def _compute_divergent_company_taxes(self):
        """Know if this product has divergent taxes across companies."""
        self.divergent_company_taxes = False
        # Skip single-company products
        if self.env["res.company"].search_count([]) == 1:
            return
        for one in self:
            if one.company_id:
                continue
            one.divergent_company_taxes = one._is_divergent_company_taxes(
                "taxes"
            ) or one._is_divergent_company_taxes("purchase")

    def _is_divergent_company_taxes(self, tax_type):
        """Returns true or false if there are differences in product taxes.

        For every other company, the taxes the product has in that company are
        compared with the taxes that ``set_multicompany_taxes`` would set there
        from the taxes of the current company.

        :param tax_type: can be 'taxes' or 'purchase'
        """
        self.ensure_one()
        if tax_type == "taxes":
            field_name = "taxes_id"
            field_name_data = "account_sale_tax_id"
        elif tax_type == "purchase":
            field_name = "supplier_taxes_id"
            field_name_data = "account_purchase_tax_id"
        else:
            raise ValueError("tax_type should be 'taxes' or 'purchase'")
        current_company = self._get_tax_source_company()
        other_companies = self.env["res.company"].search(
            [
                # Useful for tests, to avoid pollution
                ("id", "not in", self.env.context.get("ignored_company_ids", [])),
                ("id", "!=", current_company.id),
            ]
        )
        # Read the taxes of every company: the field may be read with sudo
        # (compute_sudo) or by a user that only sees the current company.
        all_taxes = self.sudo()[field_name]
        current_taxes = all_taxes.filtered(
            lambda tax: tax.company_id == current_company
        )
        # Same rule as set_multicompany_taxes: when the current company has its
        # default taxes, the other companies get their own default taxes.
        use_defaults = sorted(current_taxes.ids) == sorted(
            self._taxes_by_company(field_name_data, current_company)
        )
        for company in other_companies:
            company_taxes = set(
                all_taxes.filtered(lambda tax, c=company: tax.company_id == c).ids
            )
            # Tax-free: taxes in other companies can be propagated as empty
            if not current_taxes:
                if company_taxes:
                    return True
                continue
            if use_defaults:
                # Only taxes owned by the company: a branch uses the taxes of
                # its parent company and has none of its own.
                expected = (
                    self.env["account.tax"]
                    .sudo()
                    .browse(self._taxes_by_company(field_name_data, company))
                    .filtered(lambda tax, c=company: tax.company_id == c)
                    .ids
                )
            else:
                expected = self._taxes_by_company(
                    field_name_data, company, current_taxes.ids
                )
                # Skip companies where not every tax has an equivalent
                if len(expected) != len(current_taxes):
                    continue
            if expected and set(expected) != company_taxes:
                return True
        return False

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
        # The relations were changed in SQL: drop the cached values
        self.invalidate_recordset(fnames=["taxes_id", "supplier_taxes_id"])

    def set_multicompany_taxes(self):
        self.ensure_one()
        user_company = self._get_tax_source_company()
        # Only the taxes of the current company are the source: the fields may
        # also hold the taxes of other companies (sudo, several active companies)
        customer_tax_ids = self.taxes_id.filtered(
            lambda tax: tax.company_id == user_company
        ).ids
        supplier_tax_ids = self.supplier_taxes_id.filtered(
            lambda tax: tax.company_id == user_company
        ).ids
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
        self.sudo().write(
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
