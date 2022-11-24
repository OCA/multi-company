# Copyright 2022 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.exceptions import UserError

from odoo.addons.product_supplierinfo_group.tests.test_product_supplierinfo_group import (
    TestProductSupplierinfoGroup,
)
from odoo.addons.product_supplierinfo_intercompany.tests.test_supplier_intercompany import (
    TestIntercompanySupplierCase,
)


class IntercompanySupplierinfoGroupTest(
    TestIntercompanySupplierCase, TestProductSupplierinfoGroup
):
    @property
    def supplier_groups(self):
        return self.pricelist_intercompany.supplier_group_ids

    def test_create_delete_supplierinfo_group(self):
        """Making a pricelist intercompany should cleanup empty groups,
        reactivating it should recreate supplierinfo groups"""
        self.assertGreater(len(self.supplier_groups), 0)
        self.pricelist_intercompany.is_intercompany_supplier = False
        self.assertEqual(len(self.supplier_groups), 0)
        self.pricelist_intercompany.is_intercompany_supplier = True
        self.assertGreater(len(self.supplier_groups), 0)

    def test_raise_edit_supplierinfo_group_auto(self):
        """Automatic created supplierinfo groups: can not be edited"""
        with self.assertRaises(UserError):
            self.supplier_groups[0].product_name = "abc"

    def test_edit_supplierinfo_group_manual(self):
        """Manually created supplierinfo groups: can be edited"""
        sg = self.env["product.supplierinfo.group"].search(
            [("intercompany_pricelist_id", "=", False)], limit=1
        )
        sg.write({"sequence": 123, "product_name": "abc"})
        self.assertEqual(sg.sequence, 123)
        self.assertEqual(sg.product_name, "abc")

    def test_edit_sequence_supplierinfo_group(self):
        """Editing a sequence on an intercompany supplier group have not impact"""
        supplier_group = self.supplier_groups[0]
        supplier_group.sequence = 123
        self.assertEqual(supplier_group.sequence, -1)

    def test_edit_pricelist_supplier_sequence(self):
        self.pricelist_intercompany.supplier_sequence = -2
        self.assertEqual(set(self.supplier_groups.mapped("sequence")), {-2})

    def test_supplierinfo_group_multicompany_visibility(self):
        """Seller company (with intercompany pricelist) should not
        see its own offering as a potential supplier source"""

        self.assertTrue(self.product_template_4.supplierinfo_group_ids)

        user = self.env.ref("base.user_demo")
        user.write(
            {"groups_id": [(4, self.env.ref("sales_team.group_sale_manager").id)]}
        )
        user.company_ids = self.sale_company
        self.assertFalse(self.product_template_4.with_user(user).supplierinfo_group_ids)

    def test_add_and_update_product_item(self):
        product = self.env.ref("product.product_product_3")
        item = self._add_item(product, 22)
        self._check_supplier_info_for(product, 22)
        item.fixed_price = 30
        self._check_supplier_info_for(product, 30)
