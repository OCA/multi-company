# Copyright 2022 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import SavepointCase


class TestSalePartnerCompanyCheck(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestSalePartnerCompanyCheck, cls).setUpClass()

        cls.company_1 = cls.env["res.company"].create({"name": "company 1"})
        cls.company_2 = cls.env["res.company"].create({"name": "company 2"})
        # partner with company_id = company_1
        cls.partner = cls.env.ref("base.res_partner_address_10")

    def test_1_no_existing_sale_in_company(self):
        self.partner.company_id = self.company_1
        self.partner.company_id = self.company_2

    def test_2_existing_sale_in_company(self):
        self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        with self.assertRaises(UserError) as m:
            self.partner.write({"company_id": self.company_2.id})
        self.assertEqual(
            m.exception.name,
            "It's not possible to set the company company 2 to the "
            "record Jesse Brown as it have been used by company 1",
        )
