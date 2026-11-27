# Copyright 2026 XXP LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command


class SingleActiveCompanyCommon:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                tracking_disable=True,
                no_reset_password=True,
            )
        )
        cls.company_a = cls.env["res.company"].create({"name": "Single Active A"})
        cls.company_b = cls.env["res.company"].create({"name": "Single Active B"})
        cls.group_user = cls.env.ref("base.group_user")
        cls.group_multi_company = cls.env.ref("base.group_multi_company")
        cls.group_single_active_company = cls.env.ref(
            "res_users_single_active_company.group_single_active_company"
        )
        cls.user = cls._create_user(
            "sac_user",
            [cls.company_a, cls.company_b],
            single_active_company=True,
        )
        cls.user_plain = cls._create_user(
            "sac_user_plain",
            [cls.company_a, cls.company_b],
            single_active_company=False,
        )
        cls.env.flush_all()

    @classmethod
    def _create_user(cls, login, companies, single_active_company, groups=None):
        if groups is None:
            groups = cls.group_user | cls.group_multi_company
        if single_active_company:
            groups |= cls.group_single_active_company
        return cls.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "password": login,
                "email": "%s@example.com" % login,
                "company_id": companies[0].id,
                "company_ids": [Command.set([company.id for company in companies])],
                "groups_id": [Command.set(groups.ids)],
            }
        )
