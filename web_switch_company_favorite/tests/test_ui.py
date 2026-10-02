# Copyright 2026 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
# @author Pierre Verkest <pierre@verkest.fr>

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestResCompanyMenuUi(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company_a = cls.env["res.company"].create({"name": "Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})
        cls.company_c = cls.env["res.company"].create({"name": "Company C"})
        cls.company_d = cls.env["res.company"].create({"name": "Company D"})

        cls.demo_user = cls.env["res.users"].create(
            {
                "name": "Demo User",
                "login": "demo_user",
                "email": "demo_user@example.com",
                "password": "demo_password",
                "company_id": cls.company_a.id,
                "company_ids": [
                    (
                        6,
                        0,
                        [
                            cls.company_a.id,
                            cls.company_b.id,
                            cls.company_c.id,
                            cls.company_d.id,
                        ],
                    )
                ],
                "group_ids": [
                    (4, cls.env.ref("base.group_user").id),
                    (4, cls.env.ref("base.group_multi_company").id),
                ],
            }
        )

        cls.filter_shared = cls.env["ir.filters"].create(
            {
                "name": "Filter A and B",
                "model_id": "res.company",
                "domain": f"[('id', 'in', [{cls.company_a.id}, {cls.company_b.id}])] ",
                "user_ids": [(6, 0, [])],
            }
        )

        cls.filter_private = cls.env["ir.filters"].create(
            {
                "name": "Filter C and D",
                "model_id": "res.company",
                "domain": f"[('id', 'in', [{cls.company_c.id}, {cls.company_d.id}])] ",
                "user_ids": [(6, 0, [cls.demo_user.id])],
            }
        )

    def test_check_filter_data(self):
        res = (
            self.env["res.company"]
            .with_user(self.demo_user)
            .get_companies_from_filter(self.filter_private.id)
        )
        self.assertEqual(res, [self.company_c.id, self.company_d.id])

    def test_company_menu_favorites_apply_tour(self):
        self.start_tour("/web", "web_switch_company_favorite_apply", login="demo_user")

    def test_company_menu_favorites_create_tour(self):
        self.start_tour("/web", "web_switch_company_favorite_create", login="demo_user")

    def test_company_menu_favorites_edit_tour(self):
        self.env["ir.filters"].create(
            {
                "name": "Filter To Edit",
                "model_id": "res.company",
                "domain": "[]",
                "user_ids": [(6, 0, [])],
            }
        )
        self.start_tour("/web", "web_switch_company_favorite_edit", login="demo_user")

    def test_company_menu_favorites_delete_tour(self):
        self.env["ir.filters"].create(
            {
                "name": "Filter To Delete",
                "model_id": "res.company",
                "domain": "[]",
                "user_ids": [(6, 0, [])],
            }
        )
        self.start_tour("/web", "web_switch_company_favorite_delete", login="demo_user")
