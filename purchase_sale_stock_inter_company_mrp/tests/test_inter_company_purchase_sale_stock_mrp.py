# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.tests import Form

from odoo.addons.purchase_sale_inter_company.tests import (
    test_inter_company_purchase_sale as test_icps,
)

TestPurchaseSaleInterCompany = test_icps.TestPurchaseSaleInterCompany


class TestPurchaseSaleStockInterCompanyMrp(TestPurchaseSaleInterCompany):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create Kit and Components
        cls.kit_product = cls.env["product.product"].create(
            {"name": "Kit Product", "is_storable": False}
        )
        cls.component_1 = cls.env["product.product"].create(
            {"name": "Component 1", "is_storable": True}
        )
        cls.component_2 = cls.env["product.product"].create(
            {"name": "Component 2", "is_storable": True}
        )
        cls.component_3 = cls.env["product.product"].create(
            {"name": "Component 3", "is_storable": True}
        )
        cls.uom_box = cls.env["uom.uom"].create(
            {
                "name": "Box (10 Units)",
                "category_id": cls.env.ref("uom.product_uom_categ_unit").id,
                "factor": 0.1,
                "uom_type": "bigger",
                "rounding": 0.01,
            }
        )
        cls.partner_company_a.company_id = False
        cls.partner_company_b.company_id = False
        # One unit of component_1 and two of component_2 per kit.
        cls.bom = cls._create_bom(
            cls.kit_product,
            cls.company_b,
            [(cls.component_1, 1.0), (cls.component_2, 2.0)],
        )
        # Create PO
        po = Form(cls.env["purchase.order"])
        po.company_id = cls.company_a
        po.partner_id = cls.partner_company_b
        with po.order_line.new() as line_form:
            line_form.product_id = cls.kit_product
            line_form.product_qty = 3.0
            line_form.price_unit = 450.0
        cls.kit_po = po.save()

    @classmethod
    def _create_bom(cls, product, company, lines, product_qty=1.0, sequence=None):
        """Create a phantom BOM; lines are (product, qty[, uom]) tuples."""
        bom = Form(cls.env["mrp.bom"])
        bom.company_id = company
        bom.product_id = product
        bom.product_tmpl_id = product.product_tmpl_id
        bom.type = "phantom"
        bom.product_qty = product_qty
        for line_product, line_qty, *line_uom in lines:
            with bom.bom_line_ids.new() as line_form:
                line_form.product_id = line_product
                line_form.product_qty = line_qty
                if line_uom:
                    line_form.product_uom_id = line_uom[0]
        bom = bom.save()
        if sequence is not None:
            # Use sequence=0 for kit product to use a new bom instead of cls.bom
            bom.sequence = sequence
        return bom

    def _approve_po(self, po=None):
        """Approve the PO and return the delivery picking of its sale."""
        po = po or self.kit_po
        po.with_user(self.user_company_a).button_approve()
        sale = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", po.id)])
        )
        return sale.picking_ids[0]

    def _set_done(self, picking, quantities):
        """Set the done quantity of each move by product."""
        for product, quantity in quantities.items():
            picking.move_ids.filtered(
                lambda m, p=product: m.product_id == p
            )._set_quantity_done(quantity)

    def _assert_quantities(self, picking, expected, field="quantity"):
        for product, quantity in expected.items():
            moves = picking.move_ids.filtered(lambda m, p=product: m.product_id == p)
            self.assertAlmostEqual(sum(moves.mapped(field)), quantity)

    def _create_bom_quantity_boms(self):
        """BOMs with different quantities on each side.

        - Sale BOM (product_qty 2): 2 x component_1, 4 x component_2
          -> 1 and 2 per kit
        - Purchase BOM (product_qty 3): 3 x component_1, 6 x component_2,
          9 x component_3 -> 1, 2 and 3 per kit
        """
        self._create_bom(
            self.kit_product,
            self.company_b,
            [(self.component_1, 2.0), (self.component_2, 4.0)],
            product_qty=2.0,
            sequence=0,
        )
        self._create_bom(
            self.kit_product,
            self.company_a,
            [(self.component_1, 3.0), (self.component_2, 6.0), (self.component_3, 9.0)],
            product_qty=3.0,
        )

    def test_sale_kit(self):
        """BOM only on the sale side"""
        sale_picking = self._approve_po()
        self.assertEqual(len(sale_picking.move_ids), 2)
        # Deliver the 3 kits
        self._set_done(sale_picking, {self.component_1: 3.0, self.component_2: 6.0})
        sale_picking.button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(len(purchase_picking.move_ids), 1)
        self.assertEqual(purchase_picking.move_ids.quantity, 3.0)

    def test_sale_kit_partial(self):
        sale_picking = self._approve_po()
        self.assertEqual(len(sale_picking.move_ids), 2)
        # Deliver only 2 kits
        self._set_done(sale_picking, {self.component_1: 2.0, self.component_2: 4.0})
        sale_picking.with_context(skip_backorder=True).button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(len(purchase_picking.move_ids), 1)
        self.assertEqual(purchase_picking.move_ids.quantity, 2.0)

    def test_purchase_kit(self):
        """BOM only on the purchase side"""
        self.bom.write({"company_id": self.company_a.id})
        sale_picking = self._approve_po()
        self.assertEqual(len(sale_picking.move_ids), 1)
        # Deliver the 3 kits
        sale_picking.move_ids._set_quantity_done(3.0)
        sale_picking.button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(len(purchase_picking.move_ids), 2)
        self._assert_quantities(
            purchase_picking, {self.component_1: 3.0, self.component_2: 6.0}
        )

    def test_purchase_kit_partial(self):
        self.bom.write({"company_id": self.company_a.id})
        sale_picking = self._approve_po()
        self.assertEqual(len(sale_picking.move_ids), 1)
        # Deliver only 2 kits
        sale_picking.move_ids._set_quantity_done(2.0)
        sale_picking.with_context(skip_backorder=True).button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(len(purchase_picking.move_ids), 2)
        self._assert_quantities(
            purchase_picking, {self.component_1: 2.0, self.component_2: 4.0}
        )

    def test_purchase_kit_sync_picking(self):
        """With sync_picking enabled, validating the delivery must also
        validate the receipt of the kit components."""
        self.company_a.sync_picking = True
        self.bom.write({"company_id": self.company_a.id})
        sale_picking = self._approve_po()
        sale_picking.move_ids._set_quantity_done(3.0)
        sale_picking.button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(purchase_picking.state, "done")

    def test_sale_purchase_kit(self):
        """2 different BOMs on each side for the same kit product"""
        self._create_bom(
            self.kit_product,
            self.company_a,
            [(self.component_1, 1.0), (self.component_2, 2.0), (self.component_3, 3.0)],
        )
        sale_picking = self._approve_po()
        self.assertEqual(len(sale_picking.move_ids), 2)
        # Deliver the 3 kits
        self._set_done(sale_picking, {self.component_1: 3.0, self.component_2: 6.0})
        sale_picking.button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(len(purchase_picking.move_ids), 3)
        self._assert_quantities(
            purchase_picking,
            {self.component_1: 3.0, self.component_2: 6.0, self.component_3: 9.0},
        )

    def test_sale_purchase_kit_bom_quantity(self):
        """A BOM quantity greater than one must not be mistaken for a kit
        quantity when computing and exploding the kits."""
        self._create_bom_quantity_boms()
        # Sell four kits, i.e. two applications of the sale BOM.
        self.kit_po.order_line.product_qty = 4.0
        sale_picking = self._approve_po()
        self._assert_quantities(
            sale_picking,
            {self.component_1: 4.0, self.component_2: 8.0},
            "product_uom_qty",
        )
        # Deliver the 4 kits
        self._set_done(sale_picking, {self.component_1: 4.0, self.component_2: 8.0})
        sale_picking.button_validate()
        # The reception of the four kits requires 4, 8 and 12 purchase units.
        purchase_picking = self.kit_po.picking_ids[0]
        self._assert_quantities(
            purchase_picking,
            {self.component_1: 4.0, self.component_2: 8.0, self.component_3: 12.0},
        )

    def test_purchase_kit_other_uoms(self):
        """The kit quantities must be converted between the BOM, its lines
        and the product UoMs when syncing the destination picking."""
        # Express the kit BOM in boxes of 10 units: one box (10 kits)
        # requires 10 units of component 1 and 1 box of component 2, i.e. 1
        # unit of each per kit.
        self.bom.write(
            {"company_id": self.company_a.id, "product_uom_id": self.uom_box.id}
        )
        line_1 = self.bom.bom_line_ids.filtered(
            lambda line: line.product_id == self.component_1
        )
        line_2 = self.bom.bom_line_ids.filtered(
            lambda line: line.product_id == self.component_2
        )
        line_1.product_qty = 10.0
        line_2.product_qty = 1.0
        line_2.product_uom_id = self.uom_box
        sale_picking = self._approve_po()
        sale_picking.move_ids._set_quantity_done(3.0)
        sale_picking.button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        # 3 kits = 0.3 box: 3 units of component 1 and 0.3 box of component 2.
        self._assert_quantities(
            purchase_picking, {self.component_1: 3.0, self.component_2: 0.3}
        )
        # 0.3 box is 3 units of component_2
        self.assertAlmostEqual(
            purchase_picking.move_ids.filtered(
                lambda m: m.product_id == self.component_2
            ).product_qty,
            3.0,
        )

    def test_purchase_kit_duplicate_component(self):
        """A component repeated on several BOM lines must be split per line
        instead of receiving the full quantity on each move."""
        self.bom.write({"company_id": self.company_a.id})
        self.env["mrp.bom.line"].create(
            {
                "bom_id": self.bom.id,
                "product_id": self.component_1.id,
                "product_qty": 2.0,
            }
        )
        sale_picking = self._approve_po()
        sale_picking.move_ids._set_quantity_done(3.0)
        sale_picking.button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        component_1_moves = purchase_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_1
        )
        self.assertEqual(len(component_1_moves), 2)
        self._assert_quantities(
            purchase_picking, {self.component_1: 9.0, self.component_2: 6.0}
        )

    def test_sale_purchase_kit_optional_component(self):
        """Optional (zero-quantity) components must not change the kit
        quantity.

        component_1 is optional on the sale BOM (skipped when computing the
        delivered kits); component_2 on the purchase BOM (received at 0).
        """
        self.bom.bom_line_ids.filtered(
            lambda line: line.product_id == self.component_1
        ).product_qty = 0.0
        self._create_bom(
            self.kit_product,
            self.company_a,
            [(self.component_1, 1.0), (self.component_2, 0.0)],
        )
        sale_picking = self._approve_po()
        # On Sale side the optional component does not create a move
        self.assertEqual(len(sale_picking.move_ids), 1)
        self._set_done(sale_picking, {self.component_2: 6.0})
        sale_picking.button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        # On the Purchase side the optional component does create a move
        self.assertEqual(len(purchase_picking.move_ids), 2)
        self._assert_quantities(
            purchase_picking, {self.component_1: 3.0, self.component_2: 0.0}
        )

    def test_plain_product_sync(self):
        """A non-kit product must keep the standard quantity sync."""
        product = self.env["product.product"].create(
            {"name": "Plain Product", "is_storable": True}
        )
        po = Form(self.env["purchase.order"])
        po.company_id = self.company_a
        po.partner_id = self.partner_company_b
        with po.order_line.new() as line_form:
            line_form.product_id = product
            line_form.product_qty = 3.0
            line_form.price_unit = 10.0
        po = po.save()
        sale_picking = self._approve_po(po)
        sale_picking.move_ids._set_quantity_done(3.0)
        sale_picking.button_validate()
        purchase_picking = po.picking_ids[0]
        self.assertAlmostEqual(purchase_picking.move_ids.quantity, 3.0)
