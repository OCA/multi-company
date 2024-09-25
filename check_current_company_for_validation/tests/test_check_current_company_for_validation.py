# Copyright 2024 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestCheckCurrentCompanyForValidation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env["res.company"].create({"name": "Company"})
        cls.company_2 = cls.env["res.company"].create({"name": "Company 2"})
        cls.partner = cls.env["res.partner"].create({"name": "Partner"})
        cls.sale_order = cls.env["sale.order"].create(
            {
                "name": "SO",
                "partner_id": cls.partner.id,
                "company_id": cls.company.id,
            }
        )

    def test_check_current_company(self):
        with self.assertRaises(UserError) as m:
            self.sale_order.with_company(self.company_2.id).action_confirm()
        self.assertEqual(
            m.exception.args[0],
            "You can't validate a record from another company",
        )
        self.sale_order.action_confirm()
        self.assertEqual(self.sale_order.state, "sale")
