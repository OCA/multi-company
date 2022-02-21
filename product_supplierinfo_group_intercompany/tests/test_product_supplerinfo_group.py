# Copyright 2022 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.exceptions import UserError

from odoo.addons.product_supplier_intercompany.tests.test_supplier_intercompany import (
    TestIntercompanySupplierCase,
)
from odoo.addons.product_supplierinfo_group.tests.test_product_supplierinfo_group import (
    TestProductSupplierinfoGroup,
)


class IntercompanySupplierinfoGroupTest(
    TestIntercompanySupplierCase, TestProductSupplierinfoGroup
):
    def test_create_delete_supplierinfo_group(self):
        """Making a pricelist intercompany should cleanup empty groups,
        reactivating it should recreate supplierinfo groups"""
        sg_before = self.env["product.supplierinfo.group"].search([])
        self.pricelist_intercompany.is_intercompany_supplier = False
        sg_deleted = self.env["product.supplierinfo.group"].search([])
        # 2 products * 2 supplierinfo groups (1 for tmpl, 1 for variant) = 4
        self.assertEqual(len(sg_deleted.ids), len(sg_before) - 4)
        self.pricelist_intercompany.is_intercompany_supplier = True
        sg_re_created = self.env["product.supplierinfo.group"].search([])
        self.assertEqual(len(sg_re_created.ids), len(sg_before))

    def test_supplierinfo_group_from_pricelist_generated(self):
        """Automatically generated supplierinfo groups have correct link
        to origin pricelist"""
        self.assertEqual(
            self.product_template_4.supplierinfo_group_ids.intercompany_pricelist_id,
            self.pricelist_intercompany,
        )

    def test_edit_supplierinfo_group_auto_generated(self):
        """ Auto-generated supplierinfo groups: can edit only sequence """
        self.product_template_4.supplierinfo_group_ids[0].sequence = 123
        with self.assertRaises(UserError):
            self.product_template_4.supplierinfo_group_ids[0].product_name = "abc"

    def test_edit_supplierinfo_group_manual(self):
        """ Manually created supplierinfo groups: can edit anything """
        sg = self.env["product.supplierinfo.group"].search(
            [("intercompany_pricelist_id", "=", False)]
        )[0]
        sg.sequence = 123
        sg.product_name = "abc"

    def test_intercompany_sequence_auto_generated(self):
        """Auto-generated supplierinfo groups: should take their sequence
        from the intercompany pricelist"""
        self.pricelist_intercompany.intercompany_sequence = 3
        self.assertEqual(
            self.product_template_4.supplierinfo_group_ids[0].intercompany_sequence, -1
        )

    def test_intercompany_sequence_manual(self):
        """ Manually created supplierinfo groups: have their normal sequence """
        sequence = 9
        sg = self.env["product.supplierinfo.group"].create(
            {
                "product_tmpl_id": self.product_template_4.id,
                "partner_id": self.sale_company.id,
                "sequence": sequence,
            }
        )
        self.assertEqual(sg.intercompany_sequence, sequence)

    def test_no_self_buy(self):
        """Seller company (with intercompany pricelist) should not
        see its own offering as a potential supplier source"""

        self.assertTrue(self.product_template_4.supplierinfo_group_ids)

        user = self.env.ref("base.user_demo")
        user.write(
            {"groups_id": [(4, self.env.ref("sales_team.group_sale_manager").id)]}
        )
        user.company_ids = self.sale_company
        self.assertFalse(self.product_template_4.with_user(user).supplierinfo_group_ids)

    def test_different_pricelists_different_groups(self):
        """ Only one supplierinfo group per pricelist """
        self.assertEqual(len(self.product_template_4.supplierinfo_group_ids), 2)
        pricelist = self.env["product.pricelist"].create(
            {
                "name": "pricelist 2",
                "company_id": self.sale_company.id,
            }
        )
        self.env["product.pricelist.item"].create(
            {
                "pricelist_id": pricelist.id,
                "product_tmpl_id": self.product_template_4.id,
                "base": "list_price",
                "fixed_price": 7,
            }
        )
        pricelist.is_intercompany_supplier = True
        self.assertEqual(len(self.product_template_4.supplierinfo_group_ids), 3)
