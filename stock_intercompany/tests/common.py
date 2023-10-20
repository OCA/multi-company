from odoo.tests.common import SavepointCase


class TestStockIntercompanyCommon(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_demo = cls.env.ref("base.user_demo")
        company_obj = cls.env["res.company"]
        # Create 2 companies and configure intercompany picking type param on them
        cls.company1 = company_obj.search(
            [("name", "=", "Company A")]
        ) or company_obj.create({"name": "Company A"})
        cls.company2 = company_obj.search(
            [("name", "=", "Company B")]
        ) or company_obj.create({"name": "Company B"})
        cls.picking_type_out_company1 = (
            cls.env["stock.picking.type"]
            .sudo()
            .search(
                [
                    ("company_id", "=", cls.company1.id),
                    ("name", "=", "Delivery Orders"),
                ],
                limit=1,
            )
        )
        cls.picking_type_out_company2 = (
            cls.env["stock.picking.type"]
            .sudo()
            .search(
                [
                    ("company_id", "=", cls.company2.id),
                    ("name", "=", "Delivery Orders"),
                ],
                limit=1,
            )
        )
        cls.picking_type_in_company1 = (
            cls.env["stock.picking.type"]
            .sudo()
            .search(
                [("company_id", "=", cls.company1.id), ("name", "=", "Receipts")],
                limit=1,
            )
        )
        cls.picking_type_in_company2 = (
            cls.env["stock.picking.type"]
            .sudo()
            .search(
                [("company_id", "=", cls.company2.id), ("name", "=", "Receipts")],
                limit=1,
            )
        )

        cls.company1.intercompany_in_type_id = cls.picking_type_in_company1.id
        cls.company2.intercompany_in_type_id = cls.picking_type_in_company2.id

        cls.company1.intercompany_out_type_id = cls.picking_type_out_company1.id
        cls.company2.intercompany_out_type_id = cls.picking_type_out_company2.id
        # assign both companies to current user
        cls.user_demo.write(
            {
                "company_id": cls.company1.id,
                "company_ids": [(4, cls.company1.id), (4, cls.company2.id)],
            }
        )
        # create storable product
        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
                "categ_id": cls.env.ref("product.product_category_all").id,
                "qty_available": 100,
            }
        )
        cls.stock_location = (
            cls.env["stock.location"]
            .sudo()
            .search([("name", "=", "Stock"), ("company_id", "=", cls.company1.id)])
        )
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
