# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.fields import Command
from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class PricelistMultiCompanyCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})

        cls.user_b = new_test_user(
            cls.env,
            login="user_b_pricelist",
            groups="base.group_user,base.group_multi_company",
            company_id=cls.company_b.id,
            company_ids=[Command.set([cls.company_b.id])],
        )

        cls.pricelist_a = cls.env["product.pricelist"].create(
            {
                "name": "Pricelist A",
                "company_id": cls.company_a.id,
            }
        )
