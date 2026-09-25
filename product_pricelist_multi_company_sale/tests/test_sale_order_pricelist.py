# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.product_pricelist_multi_company.tests.common import (
    PricelistMultiCompanyCommon,
)


@tagged("post_install", "-at_install")
class TestSaleOrderPricelist(PricelistMultiCompanyCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

    def _create_order(self, company, pricelist=None):
        vals = {"partner_id": self.partner.id, "company_id": company.id}
        if pricelist:
            vals["pricelist_id"] = pricelist.id
        return self.env["sale.order"].with_company(company).create(vals)

    def test_check_company_domain_allows_shared_pricelist(self):
        self.pricelist_a.write({"company_ids": [Command.link(self.company_b.id)]})
        domain = self.pricelist_a._check_company_domain(self.company_b)
        result = self.env["product.pricelist"].search(
            list(domain) + [("id", "=", self.pricelist_a.id)]
        )
        self.assertEqual(result, self.pricelist_a)

    def test_check_company_domain_blocks_unshared_pricelist(self):
        domain = self.pricelist_a._check_company_domain(self.company_b)
        result = self.env["product.pricelist"].search(
            list(domain) + [("id", "=", self.pricelist_a.id)]
        )
        self.assertFalse(result)

    def test_sale_order_with_shared_pricelist_passes_check_company(self):
        self.pricelist_a.write({"company_ids": [Command.link(self.company_b.id)]})
        order = self._create_order(self.company_b, self.pricelist_a)
        order._check_company()

    def test_sale_order_with_unshared_pricelist_fails_check_company(self):
        order = self._create_order(self.company_b)
        with self.assertRaisesRegex(UserError, r"(?i)compan"):
            order.sudo().pricelist_id = self.pricelist_a

    def test_pricelist_field_domain_includes_shared(self):
        self.pricelist_a.write({"company_ids": [Command.link(self.company_b.id)]})
        self.assertIn(
            "company_ids",
            self.env["sale.order"]._fields["pricelist_id"].domain,
        )
        domain = [
            "|",
            "|",
            ("company_id", "=", False),
            ("company_id", "=", self.company_b.id),
            ("company_ids", "in", [self.company_b.id]),
        ]
        result = self.env["product.pricelist"].search(
            domain + [("id", "=", self.pricelist_a.id)]
        )
        self.assertEqual(result, self.pricelist_a)

    def test_pricelist_field_domain_excludes_unshared(self):
        domain = [
            "|",
            "|",
            ("company_id", "=", False),
            ("company_id", "=", self.company_b.id),
            ("company_ids", "in", [self.company_b.id]),
        ]
        result = self.env["product.pricelist"].search(
            domain + [("id", "=", self.pricelist_a.id)]
        )
        self.assertFalse(result)
