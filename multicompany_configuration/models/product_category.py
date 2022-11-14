# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ProductCategory(models.Model):

    _name = "product.category"
    _inherit = ["product.category", "multicompany.abstract"]

    def _multicompany_field_permissions(self):
        """
        Extra hook that allows us to set specific groups for company_dependent fields
        By default, we add all the modifications for odoo company dependent fields

        """
        return {
            "property_account_income_categ_id": "account.group_account_readonly",
            "property_account_expense_categ_id": "account.group_account_readonly",
            "property_account_creditor_price_difference_categ": "account."
            "group_account_readonly",
            "property_valuation": "account.group_account_readonly,stock.group_stock_manager",
            "property_stock_journal": "account.group_account_readonly",
            "property_stock_account_input_categ_id": "account.group_account_readonly",
            "property_stock_account_output_categ_id": "account.group_account_readonly",
            "property_stock_valuation_account_id": "account.group_account_readonly",
        }

    def _get_multicompany_action_xml_id(self):
        return "multicompany_configuration.product_category_form_multicompany_action"
