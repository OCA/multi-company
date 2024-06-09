# Copyright 2024 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account_invoice_inter_company.tests.test_inter_company_invoice import (
    TestAccountInvoiceInterCompanyBase,
)
from odoo.addons.product_supplierinfo_intercompany.tests.test_supplier_intercompany import (
    TestIntercompanySupplierCase,
)


class TestProductSupplierinfoIntercompanyPriority(
    TestAccountInvoiceInterCompanyBase, TestIntercompanySupplierCase
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Customer",
            }
        )
        cls.current_company = cls.env.company
        cls.other_company = cls.env["res.company"].create(
            {
                "name": "Other Company",
            }
        )
        cls.route_mto = cls.env.ref("stock.route_warehouse0_mto")
        cls.route_mto.active = True
        cls.route_buy = cls.env.ref("purchase_stock.route_warehouse0_buy")
        cls.product_template_4.write(
            {
                "route_ids": [
                    (4, cls.route_mto.id),
                    (4, cls.route_buy.id),
                ],
                "company_id": False,
            }
        )
        cls.product_4 = cls.product_template_4.product_variant_id[0]
        cls.pricelist_intercompany_bis = cls.pricelist_intercompany.copy(
            {
                "name": "Pricelist Intercompany Bis",
                "company_id": cls.other_company.id,
            }
        )
        cls.pricelist_intercompany_bis.item_ids.fixed_price = 200
        cls.purchase_company.priority_intercompany_pricelist_id = (
            cls.pricelist_intercompany_bis
        )

    @classmethod
    def create_so_return_po(cls):
        so = cls.env["sale.order"].create(
            {
                "partner_id": cls.customer.id,
                "company_id": cls.purchase_company.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_4.id,
                            "product_uom_qty": 100.0,
                        },
                    )
                ],
            }
        )
        so.action_confirm()
        return cls.env["purchase.order"].search([("origin", "=", so.name)])

    def test_priority_supplierinfo(self):
        po = self.create_so_return_po()
        self.assertEqual(po.order_line.price_unit, 200)
        self.assertEqual(po.partner_id, self.other_company.partner_id)

    def test_regular_supplier_info_by_sequence(self):
        self.purchase_company.priority_intercompany_pricelist_id = False
        po = self.create_so_return_po()
        self.assertEqual(po.order_line.price_unit, 10)
        self.assertEqual(po.partner_id, self.current_company.partner_id)

    def test_normal_purchase(self):
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.current_company.partner_id.id,
                "company_id": self.purchase_company.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_4.id,
                            "product_qty": 1.0,
                        },
                    )
                ],
            }
        )
        self.assertEqual(po.order_line.price_unit, 10)

    def test_priority_supplier_info_by_country(self):
        self.purchase_company.country_id = self.env.ref("base.fr")
        self.pricelist_intercompany.country_group_ids = self.env.ref("base.europe")
        pricelists = self.purchase_company._domain_priority_intercompany_pricelist()[0][
            2
        ]
        self.assertEqual(len(pricelists), 2)
        self.assertIn(self.pricelist_intercompany.id, pricelists)
        self.purchase_company.country_id = self.env.ref("base.us")
        pricelists = self.purchase_company._domain_priority_intercompany_pricelist()[0][
            2
        ]
        self.assertEqual(len(pricelists), 1)
        self.assertNotIn(self.pricelist_intercompany.id, pricelists)
