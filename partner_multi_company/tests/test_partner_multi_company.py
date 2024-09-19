# Copyright 2015 Oihane Crucelaegui
# Copyright 2015-2019 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, common, tagged


@tagged("post_install", "-at_install")
class TestPartnerMultiCompany(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Avoid possible spam
        cls.partner_model = cls.env["res.partner"].with_context(
            mail_create_nosubscribe=True,
        )
        cls.company_1 = cls.env["res.company"].create([{"name": "Test company 1"}])
        cls.company_2 = cls.env["res.company"].create([{"name": "Test company 2"}])
        cls.partner_company_none = cls.partner_model.create(
            [{"name": "partner without company", "company_ids": False}]
        )
        cls.partner_company_1 = cls.partner_model.create(
            [
                {
                    "name": "partner from company 1",
                    "company_ids": [Command.set(cls.company_1.ids)],
                }
            ]
        )
        cls.partner_company_2 = cls.partner_model.create(
            [
                {
                    "name": "partner from company 2",
                    "company_ids": [Command.set(cls.company_2.ids)],
                }
            ]
        )
        cls.partner_company_both = cls.partner_model.create(
            [
                {
                    "name": "partner for both companies",
                    "company_ids": [Command.set((cls.company_1 + cls.company_2).ids)],
                }
            ]
        )
        cls.user_company_1 = cls.env["res.users"].create(
            [
                {
                    "name": "User company 1",
                    "login": "user_company_1",
                    "email": "somebody@somewhere.com",
                    "groups_id": [
                        Command.link(cls.env.ref("base.group_partner_manager").id),
                        Command.link(cls.env.ref("base.group_user").id),
                    ],
                    "company_id": cls.company_1.id,
                    "company_ids": [Command.set(cls.company_1.ids)],
                }
            ]
        )
        cls.user_company_2 = cls.env["res.users"].create(
            [
                {
                    "name": "User company 2",
                    "login": "user_company_2",
                    "email": "somebody@somewhere.com",
                    "groups_id": [
                        Command.link(cls.env.ref("base.group_partner_manager").id),
                        Command.link(cls.env.ref("base.group_user").id),
                    ],
                    "company_id": cls.company_2.id,
                    "company_ids": [Command.set(cls.company_2.ids)],
                }
            ]
        )
        cls.partner_company_1 = cls.partner_company_1.with_user(cls.user_company_1)
        cls.partner_company_2 = cls.partner_company_2.with_user(cls.user_company_2)

    def test_users(self):
        self.assertEqual(self.user_company_1.partner_id.company_ids, self.company_1)
        self.assertEqual(self.user_company_2.partner_id.company_ids, self.company_2)

    def test_create_partner(self):
        partner = self.env["res.partner"].create(
            [{"name": "Test", "company_ids": [Command.link(self.env.company.id)]}]
        )
        company = self.env.company
        self.assertIn(company.id, partner.company_ids.ids)
        partner = self.env["res.partner"].create(
            [{"name": "Test 2", "company_ids": [Command.link(self.company_1.id)]}]
        )
        self.assertEqual(
            partner.with_user(self.user_company_1).company_id.id,
            self.company_1.id,
        )
        partner = self.env["res.partner"].create(
            [{"name": "Test 2", "company_ids": [Command.clear()]}]
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
            [
                {
                    "name": "Test from user company 1",
                    "company_ids": [Command.set(self.company_1.ids)],
                }
            ]
        )
        self.assertEqual(partner.company_id, self.company_1)

    def test_create_company_2(self):
        partner = self.partner_model.with_user(self.user_company_2).create(
            [
                {
                    "name": "Test from user company 2",
                    "company_ids": [Command.set(self.company_2.ids)],
                }
            ]
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

        uninstall_hook(self.env)
        rule = self.env.ref("base.res_partner_rule")
        domain = (
            "['|', '|', ('partner_share', '=', False),"
            "('company_id', 'in', company_ids),"
            "('company_id', '=', False)]"
        )
        self.assertEqual(rule.domain_force, domain)

    def test_switch_user_company(self):
        self.user_company_1.company_ids = (self.company_1 + self.company_2).ids
        self.user_company_1.company_id = self.company_2.id
        self.user_company_1 = self.user_company_1.with_user(self.user_company_2)
        self.assertEqual(
            self.user_company_1.company_id,
            self.company_2,
        )

    def test_switch_user_partner_company_form(self):
        self.user_company_1.partner_id.company_ids = self.company_1
        with Form(self.user_company_1, "base.view_users_form") as user:
            user.company_ids.add(self.company_2)
        self.assertEqual(
            self.user_company_1.partner_id.company_ids,
            self.company_1 | self.company_2,
        )
        with Form(self.user_company_1, "base.view_users_form") as user:
            user.company_ids.remove(self.company_2.id)
        self.assertEqual(
            self.user_company_1.partner_id.company_ids,
            self.company_1 | self.company_2,
        )

    def test_switch_user_partner_company_ids(self):
        self.user_company_1.partner_id.company_ids = self.company_1
        self.user_company_1.company_ids = (self.company_1 | self.company_2).ids
        self.assertEqual(
            self.user_company_1.partner_id.company_ids,
            self.company_1 | self.company_2,
        )
        self.user_company_1.company_ids = self.company_1.ids
        self.assertEqual(
            self.user_company_1.partner_id.company_ids,
            self.company_1 | self.company_2,
        )

    def test_switch_user_partner_company_set(self):
        self.user_company_1.partner_id.company_ids = self.company_1
        self.user_company_1.company_ids = [
            Command.set([self.company_1.id, self.company_2.id])
        ]
        self.assertEqual(
            self.user_company_1.partner_id.company_ids,
            self.company_1 | self.company_2,
        )
        self.user_company_1.company_ids = [Command.set([self.company_1.id])]
        self.assertEqual(
            self.user_company_1.partner_id.company_ids,
            self.company_1 | self.company_2,
        )

    def test_switch_user_partner_company_link(self):
        self.user_company_1.partner_id.company_ids = self.company_1
        self.user_company_1.company_ids = [Command.link(self.company_2.id)]
        self.assertEqual(
            self.user_company_1.partner_id.company_ids,
            self.company_1 | self.company_2,
        )
        self.user_company_1.company_ids = [Command.unlink(self.company_2.id)]
        self.assertEqual(
            self.user_company_1.partner_id.company_ids,
            self.company_1 | self.company_2,
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
            [{"name": "Child test", "parent_id": self.partner_company_both.id}]
        )
        self.assertEqual(
            partner.company_ids,
            self.partner_company_both.company_ids,
        )

    def test_avoid_updating_company_ids_in_global_partners(self):
        self.user_company_1.write({"company_ids": [Command.link(self.company_2.id)]})
        user_partner = self.user_company_1.partner_id
        user_partner.write({"company_id": False, "company_ids": [Command.clear()]})
        self.user_company_1.write({"company_id": self.company_2.id})
        self.assertEqual(user_partner.company_ids.ids, [])

    def test_partner_check_company_id(self):
        with self.assertRaisesRegex(
            ValidationError,
            "The partner must have at least all the companies associated with the user",
        ):
            self.user_company_1.partner_id.write(
                {"company_ids": [Command.set(self.company_2.ids)]}
            )
