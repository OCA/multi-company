# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Domain
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestPricelistIntercompany(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_vendor = cls.env["res.company"].create({"name": "Vendor Co"})
        cls.company_buyer_b = cls.env["res.company"].create({"name": "Buyer B"})
        cls.company_buyer_c = cls.env["res.company"].create({"name": "Buyer C"})

        cls.product = cls.env["product.template"].create(
            {
                "name": "Test Product",
                "type": "consu",
            }
        )

        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Vendor Pricelist",
                "company_id": cls.company_vendor.id,
            }
        )

    def _get_supinfos(self, pricelist_item=None, company=None):
        domain = Domain.TRUE
        if pricelist_item:
            domain &= Domain("pricelist_item_id", "=", pricelist_item.id)
        if company:
            domain &= Domain("company_id", "=", company.id)
        return self.env["product.supplierinfo"].sudo().search(domain)

    def _add_product_item(self, price=10.0):
        return self.env["product.pricelist.item"].create(
            {
                "pricelist_id": self.pricelist.id,
                "applied_on": "1_product",
                "product_tmpl_id": self.product.id,
                "compute_price": "fixed",
                "fixed_price": price,
            }
        )

    # --- creation tests ---

    def test_item_created_then_purchase_company_added(self):
        item = self._add_product_item(price=10.0)
        self.pricelist.write(
            {
                "purchase_company_ids": [Command.link(self.company_buyer_b.id)],
            }
        )
        supinfos = self._get_supinfos(pricelist_item=item, company=self.company_buyer_b)
        self.assertEqual(len(supinfos), 1)
        self.assertEqual(supinfos.partner_id, self.company_vendor.partner_id)
        self.assertAlmostEqual(
            supinfos.price, 10.0, places=supinfos.currency_id.decimal_places
        )

    def test_purchase_company_set_then_item_created(self):
        self.pricelist.write(
            {
                "purchase_company_ids": [Command.link(self.company_buyer_b.id)],
            }
        )
        item = self._add_product_item(price=15.0)
        supinfos = self._get_supinfos(pricelist_item=item, company=self.company_buyer_b)
        self.assertEqual(len(supinfos), 1)
        self.assertAlmostEqual(
            supinfos.price, 15.0, places=supinfos.currency_id.decimal_places
        )
        self.assertEqual(supinfos.partner_id, self.company_vendor.partner_id)

    def test_multiple_purchase_companies_on_create(self):
        self.pricelist.write(
            {
                "purchase_company_ids": [
                    Command.link(self.company_buyer_b.id),
                    Command.link(self.company_buyer_c.id),
                ],
            }
        )
        item = self._add_product_item(price=20.0)
        supinfos = self._get_supinfos(pricelist_item=item)
        self.assertEqual(len(supinfos), 2)
        companies = supinfos.mapped("company_id")
        self.assertIn(self.company_buyer_b, companies)
        self.assertIn(self.company_buyer_c, companies)

    # --- price update tests ---

    def test_price_update_syncs_supplierinfo(self):
        self.pricelist.write(
            {
                "purchase_company_ids": [Command.link(self.company_buyer_b.id)],
            }
        )
        item = self._add_product_item(price=10.0)
        item.write({"fixed_price": 25.0})
        supinfos = self._get_supinfos(pricelist_item=item, company=self.company_buyer_b)
        self.assertAlmostEqual(
            supinfos.price, 25.0, places=supinfos.currency_id.decimal_places
        )

    # --- deletion tests ---

    def test_item_delete_removes_supplierinfos(self):
        self.pricelist.write(
            {
                "purchase_company_ids": [Command.link(self.company_buyer_b.id)],
            }
        )
        item = self._add_product_item()
        supinfo_id = self._get_supinfos(pricelist_item=item).id
        item.unlink()
        self.assertFalse(
            self.env["product.supplierinfo"]
            .sudo()
            .search(Domain("id", "=", supinfo_id))
        )

    # --- purchase_company_ids change tests ---

    def test_add_purchase_company_creates_supplierinfos_for_existing_items(self):
        self.pricelist.write(
            {
                "purchase_company_ids": [Command.link(self.company_buyer_b.id)],
            }
        )
        item = self._add_product_item(price=10.0)
        self.pricelist.write(
            {
                "purchase_company_ids": [Command.link(self.company_buyer_c.id)],
            }
        )
        supinfos_c = self._get_supinfos(
            pricelist_item=item, company=self.company_buyer_c
        )
        self.assertEqual(len(supinfos_c), 1)
        self.assertAlmostEqual(
            supinfos_c.price, 10.0, places=supinfos_c.currency_id.decimal_places
        )
        supinfos_b = self._get_supinfos(
            pricelist_item=item, company=self.company_buyer_b
        )
        self.assertEqual(len(supinfos_b), 1)

    def test_remove_purchase_company_deletes_its_supplierinfos(self):
        self.pricelist.write(
            {
                "purchase_company_ids": [
                    Command.link(self.company_buyer_b.id),
                    Command.link(self.company_buyer_c.id),
                ],
            }
        )
        item = self._add_product_item()
        self.pricelist.write(
            {
                "purchase_company_ids": [Command.unlink(self.company_buyer_b.id)],
            }
        )
        self.assertFalse(
            self._get_supinfos(pricelist_item=item, company=self.company_buyer_b)
        )
        self.assertEqual(
            len(self._get_supinfos(pricelist_item=item, company=self.company_buyer_c)),
            1,
        )

    # --- company_id guard tests ---

    def test_change_company_blocked_when_purchase_companies_set(self):
        self.pricelist.write(
            {
                "purchase_company_ids": [Command.link(self.company_buyer_b.id)],
            }
        )
        other_company = self.env["res.company"].create({"name": "Other Vendor"})
        with self.assertRaisesRegex(UserError, "Remove the purchasing companies first"):
            self.pricelist.write({"company_id": other_company.id})

    def test_change_company_allowed_after_purchase_companies_cleared(self):
        self.pricelist.write(
            {
                "purchase_company_ids": [Command.link(self.company_buyer_b.id)],
            }
        )
        item = self._add_product_item()
        supinfo_id = self._get_supinfos(pricelist_item=item).id
        self.pricelist.write({"purchase_company_ids": [Command.clear()]})
        self.assertFalse(
            self.env["product.supplierinfo"]
            .sudo()
            .search(Domain("id", "=", supinfo_id))
        )
        other_company = self.env["res.company"].create({"name": "Other Vendor 2"})
        self.pricelist.write({"company_id": other_company.id})
        self.assertEqual(self.pricelist.company_id, other_company)

    # --- constraint tests ---

    def test_purchase_company_ids_requires_vendor_company(self):
        pricelist_no_company = self.env["product.pricelist"].create(
            {
                "name": "Shared Pricelist",
                "company_id": False,
            }
        )
        with self.assertRaisesRegex(
            ValidationError, "belongs to a specific vendor company"
        ):
            pricelist_no_company.write(
                {
                    "purchase_company_ids": [Command.link(self.company_buyer_b.id)],
                }
            )

    # --- non-product item tests ---

    def test_global_item_does_not_create_supplierinfo(self):
        self.pricelist.write(
            {
                "purchase_company_ids": [Command.link(self.company_buyer_b.id)],
            }
        )
        self.env["product.pricelist.item"].create(
            {
                "pricelist_id": self.pricelist.id,
                "applied_on": "3_global",
                "compute_price": "fixed",
                "fixed_price": 5.0,
            }
        )
        supinfos = self._get_supinfos(company=self.company_buyer_b)
        self.assertFalse(supinfos.filtered("pricelist_item_id"))

    # --- manual supplierinfo isolation ---

    def test_manual_supplierinfo_unaffected(self):
        manual_supinfo = (
            self.env["product.supplierinfo"]
            .sudo()
            .create(
                {
                    "partner_id": self.company_vendor.partner_id.id,
                    "product_tmpl_id": self.product.id,
                    "price": 99.0,
                    "company_id": self.company_buyer_b.id,
                }
            )
        )
        self.pricelist.write(
            {
                "purchase_company_ids": [Command.link(self.company_buyer_b.id)],
            }
        )
        item = self._add_product_item(price=10.0)
        item.unlink()
        self.assertTrue(
            self.env["product.supplierinfo"]
            .sudo()
            .search(Domain("id", "=", manual_supinfo.id))
        )
