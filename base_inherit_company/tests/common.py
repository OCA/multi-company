#  Copyright 2023 Simone Rubino - Aion Tech
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import tests


class Common(tests.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company_model = cls.env["res.company"]

        cls.parent_company = company_model.create(
            {
                "name": "Parent",
            }
        )
        cls.child_company, cls.sibling_company = company_model.create(
            [
                {
                    "name": "Child",
                    "parent_id": cls.parent_company.id,
                },
                {
                    "name": "Sibling",
                    "parent_id": cls.parent_company.id,
                },
            ]
        )
        cls.env.user.company_ids |= (
            cls.parent_company | cls.child_company | cls.sibling_company
        )
