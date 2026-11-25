# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.purchase_sale_inter_company.tests.test_inter_company_purchase_sale import (  # noqa: E501
    TestPurchaseSaleInterCompany,
)


class TestPurchaseSaleStockInterCompanyMrp(TestPurchaseSaleInterCompany):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (
            cls.user_company_a | cls.user_company_b | cls.intercompany_sale_user_id
        ).group_ids |= cls.env.ref("stock.group_stock_user")
        cls.kit_product, cls.component_1, cls.component_2, cls.component_3 = cls.env[
            "product.product"
        ].create(
            [
                {"name": "Kit Product", "is_storable": False},
                {"name": "Component 1", "is_storable": True},
                {"name": "Component 2", "is_storable": True},
                {"name": "Component 3", "is_storable": True},
            ]
        )
        cls.partner_company_a.company_id = False
        cls.partner_company_b.company_id = False
        cls.bom = cls._create_kit_bom(
            cls.company_b, [(cls.component_1, 1.0), (cls.component_2, 3.0)]
        )

    @classmethod
    def _create_kit_bom(cls, company, components, product_qty=1.0):
        return cls.env["mrp.bom"].create(
            {
                "company_id": company.id,
                "product_tmpl_id": cls.kit_product.product_tmpl_id.id,
                "product_id": cls.kit_product.id,
                "product_qty": product_qty,
                "type": "phantom",
                "bom_line_ids": [
                    Command.create({"product_id": product.id, "product_qty": qty})
                    for product, qty in components
                ],
            }
        )

    def _approve_kit_po(self, extra_products=None):
        po = self._create_purchase_order(
            self.partner_company_b, [self.kit_product] + (extra_products or [])
        )
        sale = self._approve_po(po)
        return po, sale.picking_ids

    def _set_done(self, picking, qty_by_product):
        for move in picking.move_ids:
            if move.product_id in qty_by_product:
                move._set_quantity_done(qty_by_product[move.product_id])
                move.picked = True

    def _assert_received(self, po, qty_by_product):
        receipt = po.picking_ids[0]
        self.assertEqual(
            {m.product_id: m.quantity if m.picked else 0.0 for m in receipt.move_ids},
            qty_by_product,
        )

    def test_sale_kit(self):
        for components_done, kits_done in [
            ({self.component_1: 3.0, self.component_2: 9.0}, 3.0),
            ({self.component_1: 2.0, self.component_2: 6.0}, 2.0),
            # Only complete kits are received
            ({self.component_1: 3.0, self.component_2: 7.0}, 2.0),
        ]:
            with self.subTest(kits_done=kits_done, components=components_done):
                po, delivery = self._approve_kit_po()
                self.assertEqual(
                    delivery.move_ids.product_id, self.component_1 | self.component_2
                )
                self._set_done(delivery, components_done)
                delivery.with_context(skip_backorder=True).button_validate()
                self._assert_received(po, {self.kit_product: kits_done})

    def test_purchase_kit(self):
        self.bom.company_id = self.company_a
        self.company_a.sync_picking = True
        for kits_done in [3.0, 2.0]:
            with self.subTest(kits_done=kits_done):
                po, delivery = self._approve_kit_po()
                self.assertEqual(delivery.move_ids.product_id, self.kit_product)
                self._set_done(delivery, {self.kit_product: kits_done})
                delivery.with_context(skip_backorder=True).button_validate()
                self._assert_received(
                    po,
                    {self.component_1: kits_done, self.component_2: kits_done * 3},
                )
                self.assertEqual(po.picking_ids[0].state, "done")
                self.assertEqual(po.order_line.qty_received, kits_done)

    def test_purchase_kit_bom_quantity(self):
        self.bom.write({"company_id": self.company_a.id, "product_qty": 2.0})
        po, delivery = self._approve_kit_po()
        self._set_done(delivery, {self.kit_product: 2.0})
        delivery.with_context(skip_backorder=True).button_validate()
        self._assert_received(po, {self.component_1: 1.0, self.component_2: 3.0})

    def test_purchase_kit_other_line_not_delivered(self):
        self.bom.company_id = self.company_a
        po, delivery = self._approve_kit_po(extra_products=[self.component_3])
        self._set_done(delivery, {self.kit_product: 2.0})
        delivery.with_context(
            skip_backorder=True, picking_ids_not_to_backorder=delivery.ids
        ).button_validate()
        self._assert_received(
            po,
            {self.component_1: 2.0, self.component_2: 6.0, self.component_3: 0.0},
        )

    def test_sale_purchase_kit(self):
        self._create_kit_bom(
            self.company_a,
            [(self.component_1, 1.0), (self.component_2, 2.0), (self.component_3, 5.0)],
        )
        po, delivery = self._approve_kit_po()
        self._set_done(delivery, {self.component_1: 3.0, self.component_2: 9.0})
        delivery.button_validate()
        self._assert_received(
            po,
            {self.component_1: 3.0, self.component_2: 6.0, self.component_3: 15.0},
        )

    def test_kit_inter_company_transit_backorder(self):
        self.company_a.sync_picking = True
        self.company_a._set_per_company_inter_company_locations(
            self.env.ref("stock.stock_location_inter_company")
        )
        kit = {self.kit_product: 1.0}
        components = {self.component_1: 1.0, self.component_2: 3.0}
        # Purchase kit first: no component stock yet in the transit location
        for kit_company, delivered, received in [
            (self.company_a, kit, components),
            (self.company_b, components, kit),
        ]:
            with self.subTest(kit_company=kit_company.name):
                self.bom.company_id = kit_company
                po, delivery = self._approve_kit_po()
                self._set_done(delivery, {p: q * 2 for p, q in delivered.items()})
                delivery.with_context(skip_backorder=True).button_validate()
                backorder = delivery.backorder_ids
                self._set_done(backorder, {p: q for p, q in delivered.items()})
                backorder.button_validate()
                receipts = po.picking_ids.sorted("id")
                self.assertEqual(receipts.location_id.usage, "transit")
                self.assertEqual(receipts.mapped("state"), ["done", "done"])
                for receipt, factor in zip(receipts, [2, 1], strict=True):
                    self.assertEqual(
                        {m.product_id: m.quantity for m in receipt.move_ids},
                        {p: q * factor for p, q in received.items()},
                    )
                self.assertEqual(po.order_line.qty_received, 3.0)
