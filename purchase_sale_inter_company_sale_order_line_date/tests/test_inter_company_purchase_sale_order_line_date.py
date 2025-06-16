# Copyright 2013-Today Odoo SA
# Copyright 2019-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.addons.purchase_sale_inter_company.tests.test_inter_company_purchase_sale import (
    TestPurchaseSaleInterCompany,
)


class TestPurchaseSaleInterCompanySaleOrderLineDate(TestPurchaseSaleInterCompany):
    def test_commitment_date_synced_from_date_planned(self):
        # Set a specific date_planned on the purchase order line
        date_planned = datetime(2080, 1, 1, 0, 0)
        self.purchase_company_a.order_line.date_planned = date_planned

        # Approve the purchase order to trigger SO creation/sync
        sale = self._approve_po()

        # Check that the SO's line commitment_date matches the PO's line date_planned
        self.assertEqual(sale.order_line.commitment_date, date_planned)
