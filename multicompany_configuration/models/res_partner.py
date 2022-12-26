# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "multicompany.abstract"]

    def _multicompany_field_permissions(self):
        """
        Extra hook that allows us to set specific groups for company_dependent fields
        By default, we add all the modifications for odoo company dependent fields

        """
        return {
            # account fields
            "property_account_payable_id": "account.group_account_readonly",
            "property_account_receivable_id": "account.group_account_readonly",
            "property_account_position_id": "account.group_account_invoice,"
            "sales_team.group_sale_salesman",
            "property_payment_term_id": "account.group_account_invoice,"
            "sales_team.group_sale_salesman",
            "property_supplier_payment_term_id": "account.group_account_invoice,"
            "account.group_account_readonly",
            "invoice_warn": "account.group_warning_account",
            "property_payment_method_id": "account.group_account_invoice,"
            "account.group_account_readonly",
            # mrp
            "property_stock_subcontractor": "base.group_no_one",
            # product
            "property_product_pricelist": "product.group_product_pricelist",
            # purchase
            "property_purchase_currency_id": "base.group_multi_currency",
            "receipt_reminder_email": "purchase.group_send_reminder",
            "reminder_date_before_receipt": "purchase.group_send_reminder",
            # stock
            "property_stock_customer": "base.group_no_one",
            "property_stock_supplier": "base.group_no_one",
            # base fields
            "barcode": "point_of_sale.group_pos_user",
        }

    def _get_multicompany_action_xml_id(self):
        return "multicompany_configuration.res_partner_form_multicompany_action"
