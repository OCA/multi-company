# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tools.misc import unquote

from .common import PricelistMultiCompanyCommon


@tagged("post_install", "-at_install")
class TestProductPricelistMultiCompany(PricelistMultiCompanyCommon):
    def test_company_id_auto_added_to_company_ids(self):
        self.assertIn(self.company_a, self.pricelist_a.company_ids)

    def test_pricelist_not_visible_to_other_company_by_default(self):
        result = (
            self.env["product.pricelist"]
            .with_user(self.user_b)
            .search([("id", "=", self.pricelist_a.id)])
        )
        self.assertFalse(result)

    def test_share_pricelist_with_other_company(self):
        self.pricelist_a.write({"company_ids": [Command.link(self.company_b.id)]})
        result = (
            self.env["product.pricelist"]
            .with_user(self.user_b)
            .search([("id", "=", self.pricelist_a.id)])
        )
        self.assertEqual(result, self.pricelist_a)

    def test_unshare_removes_visibility(self):
        self.pricelist_a.write({"company_ids": [Command.link(self.company_b.id)]})
        self.pricelist_a.write({"company_ids": [Command.unlink(self.company_b.id)]})
        result = (
            self.env["product.pricelist"]
            .with_user(self.user_b)
            .search([("id", "=", self.pricelist_a.id)])
        )
        self.assertFalse(result)

    def test_pricelist_item_not_visible_to_other_company_by_default(self):
        item = self.env["product.pricelist.item"].create(
            {
                "pricelist_id": self.pricelist_a.id,
                "compute_price": "fixed",
                "fixed_price": 10.0,
                "applied_on": "3_global",
            }
        )
        result = (
            self.env["product.pricelist.item"]
            .with_user(self.user_b)
            .search([("id", "=", item.id)])
        )
        self.assertFalse(result)

    def test_pricelist_item_visible_when_pricelist_shared(self):
        item = self.env["product.pricelist.item"].create(
            {
                "pricelist_id": self.pricelist_a.id,
                "compute_price": "fixed",
                "fixed_price": 10.0,
                "applied_on": "3_global",
            }
        )
        self.pricelist_a.write({"company_ids": [Command.link(self.company_b.id)]})
        item.invalidate_recordset()
        result = (
            self.env["product.pricelist.item"]
            .with_user(self.user_b)
            .search([("id", "=", item.id)])
        )
        self.assertEqual(result, item)

    def test_item_company_ids_mirrors_pricelist(self):
        item = self.env["product.pricelist.item"].create(
            {
                "pricelist_id": self.pricelist_a.id,
                "compute_price": "fixed",
                "fixed_price": 10.0,
                "applied_on": "3_global",
            }
        )
        self.pricelist_a.write({"company_ids": [Command.link(self.company_b.id)]})
        item.invalidate_recordset()
        self.assertEqual(item.company_ids, self.pricelist_a.company_ids)

    def test_partner_pricelist_hook_includes_shared_pricelist(self):
        self.pricelist_a.write({"company_ids": [Command.link(self.company_b.id)]})
        PL = self.env["product.pricelist"].with_company(self.company_b)
        domain = PL._get_partner_pricelist_multi_search_domain_hook(self.company_b.id)
        result = PL.search(domain + [("id", "=", self.pricelist_a.id)])
        self.assertEqual(result, self.pricelist_a)

    def test_partner_pricelist_hook_excludes_unshared_pricelist(self):
        PL = self.env["product.pricelist"].with_company(self.company_b)
        domain = PL._get_partner_pricelist_multi_search_domain_hook(self.company_b.id)
        result = PL.search(domain + [("id", "=", self.pricelist_a.id)])
        self.assertFalse(result)

    def test_global_pricelist_visible_to_all_companies(self):
        global_pricelist = self.env["product.pricelist"].create(
            {"name": "Global", "company_id": False}
        )
        result = (
            self.env["product.pricelist"]
            .with_user(self.user_b)
            .search([("id", "=", global_pricelist.id)])
        )
        self.assertEqual(result, global_pricelist)

    def test_global_pricelist_has_empty_company_ids(self):
        global_pricelist = self.env["product.pricelist"].create(
            {"name": "Global", "company_id": False}
        )
        self.assertFalse(global_pricelist.company_ids)

    def test_clearing_company_id_clears_company_ids(self):
        self.pricelist_a.write(
            {"company_ids": [fields.Command.link(self.company_b.id)]}
        )
        self.pricelist_a.company_id = False
        self.assertFalse(self.pricelist_a.company_ids)

    def test_check_company_domain_empty_companies_returns_super_domain(self):
        domain = self.pricelist_a._check_company_domain(False)
        result = self.env["product.pricelist"].search(
            list(domain) + [("id", "=", self.pricelist_a.id)]
        )
        self.assertFalse(result)

    def test_check_company_domain_unquote_includes_company_ids_leaf(self):
        domain = self.pricelist_a._check_company_domain(unquote("company_ids"))
        self.assertIn("company_ids", str(domain))

    def test_check_company_domain_int_allows_shared_pricelist(self):
        self.pricelist_a.write({"company_ids": [Command.link(self.company_b.id)]})
        domain = self.pricelist_a._check_company_domain(self.company_b.id)
        result = self.env["product.pricelist"].search(
            list(domain) + [("id", "=", self.pricelist_a.id)]
        )
        self.assertEqual(result, self.pricelist_a)

    def test_check_company_domain_list_allows_shared_pricelist(self):
        self.pricelist_a.write({"company_ids": [Command.link(self.company_b.id)]})
        domain = self.pricelist_a._check_company_domain([self.company_b.id])
        result = self.env["product.pricelist"].search(
            list(domain) + [("id", "=", self.pricelist_a.id)]
        )
        self.assertEqual(result, self.pricelist_a)
