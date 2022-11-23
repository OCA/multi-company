from odoo.exceptions import AccessError
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestPartnerMultiCompany(common.TransactionCase):
    def setUp(self):
        super(TestPartnerMultiCompany, self).setUp()
        # Avoid possible spam
        self.partner_model = self.env["res.partner"].with_context(
            mail_create_nosubscribe=True,
        )
        self.company_1 = self.env["res.company"].create({"name": "Test company 1"})
        self.company_2 = self.env["res.company"].create({"name": "Test company 2"})
        self.partner_company_none = self.partner_model.create(
            {"name": "partner without company", "company_ids": False}
        )
        self.partner_company_1 = self.partner_model.create(
            {
                "name": "partner from company 1",
                "company_ids": [(6, 0, self.company_1.ids)],
            }
        )
        self.partner_company_2 = self.partner_model.create(
            {
                "name": "partner from company 2",
                "company_ids": [(6, 0, self.company_2.ids)],
            }
        )
        self.partner_company_both = self.partner_model.create(
            {
                "name": "partner for both companies",
                "company_ids": [(6, 0, (self.company_1 + self.company_2).ids)],
            }
        )
        self.user_company_1 = self.env["res.users"].create(
            {
                "name": "User company 1",
                "login": "user_company_1",
                "email": "somebody@somewhere.com",
                "groups_id": [
                    (4, self.env.ref("base.group_partner_manager").id),
                    (4, self.env.ref("base.group_user").id),
                ],
                "company_id": self.company_1.id,
                "company_ids": [(6, 0, self.company_1.ids)],
            }
        )
        self.user_company_2 = self.env["res.users"].create(
            {
                "name": "User company 2",
                "login": "user_company_2",
                "email": "somebody@somewhere.com",
                "groups_id": [
                    (4, self.env.ref("base.group_partner_manager").id),
                    (4, self.env.ref("base.group_user").id),
                ],
                "company_id": self.company_2.id,
                "company_ids": [(6, 0, self.company_2.ids)],
            }
        )
        self.partner_company_1 = self.partner_company_1.with_user(self.user_company_1)
        self.partner_company_2 = self.partner_company_2.with_user(self.user_company_2)

    def test_create_partner(self):
        partner = self.env["res.partner"].create(
            {"name": "Test", "company_ids": [(4, self.env.company.id)]}
        )
        company = self.env.company
        self.assertIn(company.id, partner.company_ids.ids)
        partner = self.env["res.partner"].create(
            {"name": "Test 2", "company_ids": [(4, self.company_1.id)]}
        )
        self.assertEqual(
            partner.with_user(self.user_company_1).company_id.id,
            self.company_1.id,
        )
        partner = self.env["res.partner"].create(
            {"name": "Test 2", "company_ids": [(5, False)]}
        )
        self.assertFalse(partner.company_id)

    def test_company_none(self):
        self.assertFalse(self.partner_company_none.company_id)
        # All of this should be allowed
        self.partner_company_none.with_user(self.user_company_1.id).name = "Test"
        self.partner_company_none.with_user(self.user_company_2.id).name = "Test"

    def test_company_1(self):
        self.assertEqual(self.partner_company_1.company_id, self.company_1)
        # All of this should be allowed
        self.partner_company_1.with_user(self.user_company_1).name = "Test"
        self.partner_company_both.with_user(self.user_company_1).name = "Test"
        # And this one not
        with self.assertRaises(AccessError):
            self.partner_company_2.with_user(self.user_company_1).name = "Test"

    def test_create_company_1(self):
        partner = self.partner_model.with_user(self.user_company_1).create(
            {
                "name": "Test from user company 1",
                "company_ids": [(6, 0, self.company_1.ids)],
            }
        )
        self.assertEqual(partner.company_id, self.company_1)

    def test_create_company_2(self):
        partner = self.partner_model.with_user(self.user_company_2).create(
            {
                "name": "Test from user company 2",
                "company_ids": [(6, 0, self.company_2.ids)],
            }
        )
        self.assertEqual(partner.company_id, self.company_2)

    def test_company_2(self):
        self.assertEqual(self.partner_company_2.company_id, self.company_2)
        # All of this should be allowed
        self.partner_company_2.with_user(self.user_company_2).name = "Test"
        self.partner_company_both.with_user(self.user_company_2).name = "Test"
        # And this one not
        with self.assertRaises(AccessError):
            self.partner_company_1.with_user(self.user_company_2).name = "Test"

    def test_uninstall(self):
        from ..hooks import uninstall_hook

        uninstall_hook(self.env.cr, None)
        rule = self.env.ref("base.res_partner_rule")
        domain = (
            "['|','|',"
            "('company_id.child_ids','child_of',[user.company_id.id]),"
            "('company_id','child_of',[user.company_id.id]),"
            "('company_id','=',False)]"
        )
        self.assertEqual(rule.domain_force, domain)
        self.assertFalse(rule.active)

    def test_switch_user_company(self):
        self.user_company_1.company_ids = (self.company_1 + self.company_2).ids
        self.user_company_1.company_id = self.company_2.id
        self.user_company_1 = self.user_company_1.with_user(self.user_company_2)
        self.assertEqual(
            self.user_company_1.company_id,
            self.company_2,
        )

    def test_commercial_fields_implementation(self):
        """It should add company_ids to commercial fields."""
        self.assertIn(
            "company_ids",
            self.env["res.partner"]._commercial_fields(),
        )

    def test_commercial_fields_result(self):
        """It should add company_ids to children partners."""
        partner = self.env["res.partner"].create(
            {"name": "Child test", "parent_id": self.partner_company_both.id}
        )
        self.assertEqual(
            partner.company_ids,
            self.partner_company_both.company_ids,
        )

    def test_avoid_updating_company_ids_in_global_partners(self):
        self.user_company_1.write({"company_ids": [(4, self.company_2.id)]})
        user_partner = self.user_company_1.partner_id
        user_partner.write({"company_id": False, "company_ids": [(5, False)]})
        self.user_company_1.write({"company_id": self.company_2.id})
        self.assertEqual(user_partner.company_ids.ids, [])
