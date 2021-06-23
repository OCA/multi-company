# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


class ProductMultiCompanyCommon(object):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        groups = cls.env.ref("base.group_system")
        cls.product_obj = cls.env["product.product"]
        cls.company_obj = cls.env["res.company"]
        cls.company_1 = cls.company_obj.create({"name": "Test company 1"})
        cls.company_2 = cls.company_obj.create({"name": "Test company 2"})
        cls.product_company_none = cls.product_obj.create(
            {
                "name": "Product without company",
                "company_ids": [(6, 0, [])],
                "company_id": False,
            }
        )
        cls.product_company_1 = cls.product_obj.create(
            {
                "name": "Product from company 1",
                "company_ids": [(6, 0, cls.company_1.ids)],
            }
        )
        cls.product_company_2 = cls.product_obj.create(
            {
                "name": "Product from company 2",
                "company_ids": [(6, 0, cls.company_2.ids)],
            }
        )
        cls.product_company_both = cls.product_obj.create(
            {
                "name": "Product for both companies",
                "company_ids": [(6, 0, (cls.company_1 + cls.company_2).ids)],
            }
        )
        cls.user_company_1 = cls.env["res.users"].create(
            {
                "name": "User company 1",
                "login": "user_company_1",
                "groups_id": [(6, 0, groups.ids)],
                "company_id": cls.company_1.id,
                "company_ids": [(6, 0, cls.company_1.ids)],
            }
        )
        cls.user_company_2 = cls.env["res.users"].create(
            {
                "name": "User company 2",
                "login": "user_company_2",
                "groups_id": [(6, 0, groups.ids)],
                "company_id": cls.company_2.id,
                "company_ids": [(6, 0, cls.company_2.ids)],
            }
        )
