# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.purchase_sale_inter_company.tests.common import (
    BasePurchaseSaleInterCompany,
)


class TestPurchaseSaleNoteIntercompany(BasePurchaseSaleInterCompany):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.purchase_company_a.order_line[0].note = "Some details"

    def test_propagated_note_intercompany(self):
        sale = self._approve_po()
        self.assertEqual(sale.order_line[0].note, "Some details")
