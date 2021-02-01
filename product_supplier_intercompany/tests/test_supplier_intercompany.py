# Copyright 2019 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import Warning as UserError
from odoo.tests.common import TransactionCase


class TestPricelist(TransactionCase):
    def setUp(self):
        super(TestPricelist, self).setUp()

        # configure multi company environment
        self.env["product.template"].search([]).write({"company_id": False})

        self.user = self.env.ref("base.user_demo")
        self.user.write(
            {"groups_id": [(4, self.env.ref("sales_team.group_sale_manager").id)]}
        )
        self.env = self.env(user=self.user)
        ref = self.env.ref
        self.pricelist_intercompany = ref(
            "product_supplier_intercompany.pricelist_intercompany"
        )
        self.pricelist_not_intercompany = ref(
            "product_supplier_intercompany.pricelist_not_intercompany"
        )
        self.partner = ref("base.main_partner")

        self.product_template_4 = ref("product.product_product_4_product_template")
        self.product_product_4b = ref("product.product_product_4b")
        self.product_product_4c = ref("product.product_product_4c")

        self.product_template_1 = ref("product.product_product_1_product_template")
        self.product_product_2 = ref("product.product_product_2")

        self.pricelist_item_4 = ref(
            "product_supplier_intercompany.pricelist_item_product_template_4"
        )
        self.pricelist_item_4b = ref(
            "product_supplier_intercompany.pricelist_item_product_product_4b"
        )

        self.sale_company = ref("base.main_company")
        self.purchase_company = ref("product_supplier_intercompany.purchaser_company")
        self.supplier_info = self._get_supplier_info(self.product_template_1)

    def _get_supplier_info(self, record=None, sudo=True):
        domain = [
            ("name", "=", self.partner.id),
            ("intercompany_pricelist_id", "=", self.pricelist_intercompany.id),
            ("company_id", "=", False),
        ]
        if record:
            self.assertIn(record._name, ["product.product", "product.template"])
            if record._name == "product.product":
                domain += [
                    ("product_tmpl_id", "=", record.product_tmpl_id.id),
                    ("product_id", "=", record.id),
                ]
            else:
                domain += [
                    ("product_tmpl_id", "=", record.id),
                    ("product_id", "=", False),
                ]
        supplierinfo_obj = self.env["product.supplierinfo"]
        if sudo:
            supplierinfo_obj = supplierinfo_obj.sudo()
        res = supplierinfo_obj.search(domain)
        return res

    def _check_no_supplier_info_for(self, record):
        supplierinfo = self._get_supplier_info(record)
        self.assertEqual(len(supplierinfo), 0)

    def _check_supplier_info_for(self, record, price):
        supplierinfo = self._get_supplier_info(record)
        self.assertEqual(len(supplierinfo), 1)
        self.assertEqual(len(supplierinfo.intercompany_pricelist_id), 1)
        self.assertEqual(supplierinfo.price, price)

    def _add_item(self, record, price, pricelist_id=None):
        ref = self.env.ref
        pricelist_id = (
            pricelist_id
            or ref("product_supplier_intercompany.pricelist_intercompany").id
        )
        self.assertIn(record._name, ["product.product", "product.template"])
        vals = {
            "pricelist_id": pricelist_id,
            "base": "list_price",
            "price_discount": 0,
            "fixed_price": price,
        }
        if record._name == "product.product":
            vals.update(
                {
                    "product_id": record.id,
                    "product_tmpl_id": record.product_tmpl_id.id,
                }
            )
        else:
            vals["product_tmpl_id"] = record.id
        res = self.env["product.pricelist.item"].create(vals)
        return res

    def _switch_user_to_purchase_company(self):
        self.user.write(
            {
                "company_id": self.purchase_company.id,
                "company_ids": [
                    (6, 0, [self.purchase_company.id, self.sale_company.id])
                ],
            }
        )

    def test_set_pricelist_as_intercompany(self):
        supplierinfo = self._get_supplier_info()
        self.assertEqual(len(supplierinfo), 4)
        self._check_supplier_info_for(self.product_template_4, 10)
        self._check_supplier_info_for(self.product_product_4b, 15)
        self._check_supplier_info_for(self.product_template_1, 5)
        self._check_supplier_info_for(self.product_product_2, 20)

    def test_unset_pricelist_intercompany(self):
        self.pricelist_intercompany.is_intercompany_supplier = False
        supplierinfo = self._get_supplier_info()
        self.assertEqual(len(supplierinfo), 0)

    def test_intercompany_access_rule(self):
        # Check that supplier this supplier info are not visible
        # with the current user "demo"
        supplierinfo = self._get_supplier_info(sudo=False)
        self.assertEqual(len(supplierinfo), 0)
        # Switch the company and check that the user can now see the supplier
        self._switch_user_to_purchase_company()
        supplierinfo = self._get_supplier_info(sudo=False)
        self.assertEqual(len(supplierinfo), 4)

    def test_add_product_item(self):
        product = self.env.ref("product.product_product_3")
        self._add_item(product, 22)
        self._check_supplier_info_for(product, 22)

    def test_add_template_item(self):
        template = self.env.ref("product.product_product_2_product_template")
        self._add_item(template, 30)
        self._check_supplier_info_for(template, 30)

    def test_update_product_item(self):
        self.pricelist_item_4b.fixed_price = 40
        self._check_supplier_info_for(self.product_product_4b, 40)

    def test_change_product_item(self):
        self.pricelist_item_4b.product_id = self.product_product_4c
        self._check_no_supplier_info_for(self.product_product_4b)
        self._check_supplier_info_for(self.product_product_4c, 15)

    def test_update_template_item(self):
        self.pricelist_item_4.fixed_price = 40
        self._check_supplier_info_for(self.product_template_4, 40)

    def test_add_product_item_different_unit(self):
        product = self.env.ref("product.product_product_3")
        uom_dozen = self.env.ref("uom.product_uom_dozen")
        product.uom_po_id = uom_dozen
        self._add_item(product, 100)
        self._check_supplier_info_for(product, 1200)

    def test_remove_product_item(self):
        self.pricelist_item_4b.unlink()
        self._check_no_supplier_info_for(self.product_product_4b)

    def test_remove_template_item(self):
        self.pricelist_item_4.unlink()
        self._check_no_supplier_info_for(self.product_template_4)

    def test_raise_error_unlink_supplierinfo(self):
        with self.assertRaises(UserError):
            self.supplier_info.unlink()

    def test_raise_error_unlink_supplierinfo_items(self):
        with self.assertRaises(UserError):
            self.supplier_info.unlink()

    def test_raise_error_write_supplierinfo(self):
        with self.assertRaises(UserError):
            self.supplier_info.write({"product_code": "TEST"})

    def test_raise_error_write_supplierinfo_items(self):
        with self.assertRaises(UserError):
            self.supplier_info.write({"price": 100})

    def test_raise_error_create_supplierinfo(self):
        with self.assertRaises(UserError):
            pricelist = self.pricelist_intercompany.id
            self.env["product.supplierinfo"].sudo().create(
                {
                    "company_id": False,
                    "name": self.partner.id,
                    "product_tmpl_id": self.product_template_1.id,
                    "intercompany_pricelist_id": pricelist,
                }
            )

    def test_add_product_item_no_intercompany(self):
        product = self.env.ref("product.product_product_3")
        nbr_supplier = self.env["product.supplierinfo"].sudo().search_count([])
        self._add_item(
            product,
            30,
            pricelist_id=self.pricelist_not_intercompany.id,
        )
        self.assertEqual(
            nbr_supplier,
            self.env["product.supplierinfo"].sudo().search_count([]),
        )

    def test_raise_error_forcing_recompute_with_not_intercompany(self):
        with self.assertRaises(UserError):
            product = self.env.ref("product.product_product_3")
            self._add_item(
                product,
                30,
                pricelist_id=self.pricelist_not_intercompany.id,
            )
            product._synchronise_supplier_info(
                pricelists=self.pricelist_not_intercompany
            )

    def test_add_product_item_no_intercompany_empty_todo(self):
        product = self.env.ref("product.product_product_3")
        item = self._add_item(
            product,
            30,
            pricelist_id=self.pricelist_not_intercompany.id,
        )
        todo = {}
        item._add_product_to_synchronize(todo)
        self.assertEqual(todo, {})

    def test_raise_error_required_company(self):
        with self.assertRaises(UserError):
            self.pricelist_intercompany.company_id = False
