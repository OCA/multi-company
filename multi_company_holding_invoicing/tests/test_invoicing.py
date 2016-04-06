# -*- coding: utf-8 -*-
# © 2016 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from .common import (
    CommonInvoicing,
    XML_SECTION_1,
    XML_SECTION_2,
    XML_COMPANY_A,
    XML_COMPANY_B,
    XML_COMPANY_HOLDING,
    XML_PARTNER_ID,
    )


class TestInvoicing(CommonInvoicing):

    def test_invoice_market_1_one_company_one_partner(self):
        self._set_partner([1, 2, 3, 4], XML_PARTNER_ID)
        self._set_section([1, 2], XML_SECTION_1)
        self._set_section([3, 4], XML_SECTION_2)
        self._set_company([1, 2, 3, 4], XML_COMPANY_A)
        self._process_and_check_sale(XML_SECTION_1, [1, 2, 3, 4], [1, 2])
        sales = self._get_sales([3, 4])
        self._check_sale_state(sales, 'invoiceable')

    def test_invoice_market_1_multi_company_one_partner(self):
        self._set_partner([1, 2, 3, 4], XML_PARTNER_ID)
        self._set_section([1, 2, 3, 4], XML_SECTION_1)
        self._set_company([1, 2], XML_COMPANY_A)
        self._set_company([3, 4], XML_COMPANY_B)
        self._process_and_check_sale(XML_SECTION_1, [1, 2, 3, 4], [1, 2, 3, 4])

    def test_invoice_market_1_multi_company_with_holding_one_partner(self):
        self._set_partner([1, 2, 3, 4], XML_PARTNER_ID)
        self._set_section([1, 2, 3, 4], XML_SECTION_1)
        self._set_company([1, 2], XML_COMPANY_A)
        self._set_company([3], XML_COMPANY_B)
        self._set_company([4], XML_COMPANY_HOLDING)
        self._process_and_check_sale(XML_SECTION_1, [1, 2, 3, 4], [1, 2, 3])
        sales = self._get_sales([4])
        self._check_sale_state(sales, 'none')

    def test_invoice_market_1_one_company_one_partner_by_sale(self):
        section = self.env.ref(XML_SECTION_1)
        section.write({'holding_invoice_group_by': 'sale'})
        self.test_invoice_market_1_one_company_one_partner()

    def test_invoice_market_1_multi_company_one_partner_by_sale(self):
        section = self.env.ref(XML_SECTION_1)
        section.write({'holding_invoice_group_by': 'sale'})
        self.test_invoice_market_1_multi_company_one_partner()

    def test_invoice_market_1_multi_company_with_holding_one_partner_by_sale(
            self):
        section = self.env.ref(XML_SECTION_1)
        section.write({'holding_invoice_group_by': 'sale'})
        self.test_invoice_market_1_multi_company_with_holding_one_partner()
