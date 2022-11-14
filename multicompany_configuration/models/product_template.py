# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ProductTemplate(models.Model):

    _name = "product.template"
    _inherit = ["product.template", "multicompany.abstract"]

    def _multicompany_field_permissions(self):
        """
        Extra hook that allows us to set specific groups for company_dependent fields
        By default, we add all the modifications for odoo company dependent fields

        """
        return {
            "property_account_income_id": "account.group_account_readonly",
            "property_account_expense_id": "account.group_account_readonly",
            "property_account_creditor_price_difference": "account.group_account_readonly",
            "property_stock_production": "base.group_no_one",
            "property_stock_inventory": "base.group_no_one",
        }

    def _get_multicompany_action_xml_id(self):
        return "multicompany_configuration.product_template_form_multicompany_action"


class ProductProduct(models.Model):

    _name = "product.product"
    _inherit = ["product.product", "multicompany.abstract"]

    def _multicompany_field_permissions(self):
        """
        Extra hook that allows us to set specific groups for company_dependent fields
        By default, we add all the modifications for odoo company dependent fields

        """
        result = self.product_tmpl_id._multicompany_field_permissions()
        result.update({})
        return result

    def _get_multicompany_action_xml_id(self):
        return "multicompany_configuration.product_product_form_multicompany_action"
