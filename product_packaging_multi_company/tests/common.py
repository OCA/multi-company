from odoo.tests import common


class ProductPackagingMultiCompanyCommon(common.TransactionCase):
    @classmethod
    def _create_companies(cls):
        cls.company_obj = cls.env["res.company"]
        cls.company_1 = cls.company_obj.create(
            {
                "name": "Test company 1",
                "currency_id": cls.env.ref("base.USD").id,
            }
        )
        cls.company_2 = cls.company_obj.create(
            {
                "name": "Test company 2",
                "currency_id": cls.env.ref("base.USD").id,
            }
        )

    @classmethod
    def _create_users(cls):
        cls.user_company_1 = cls.env["res.users"].create(
            {
                "name": "User company 1",
                "login": "user_packaging_company_1",
                "groups_id": [(6, 0, cls.groups.ids)],
                "company_id": cls.company_1.id,
                "company_ids": [(6, 0, cls.company_1.ids)],
            }
        )
        cls.user_company_2 = cls.env["res.users"].create(
            {
                "name": "User company 2",
                "login": "user_packaging_company_2",
                "groups_id": [(6, 0, cls.groups.ids)],
                "company_id": cls.company_2.id,
                "company_ids": [(6, 0, cls.company_2.ids)],
            }
        )

    @classmethod
    def _create_products(cls):
        Product = cls.env["product.product"]
        cls.product_company_1 = Product.create(
            {"name": "Test Product 1", "type": "consu", "company_id": cls.company_1.id}
        )
        cls.product_company_2 = Product.create(
            {"name": "Test Product 2", "type": "consu", "company_id": cls.company_2.id}
        )
        cls.product_no_company = Product.create(
            {"name": "Product no company", "type": "consu", "company_id": False}
        )

    @classmethod
    def _create_package_types(cls):
        cls.package_type_obj = cls.env["stock.package.type"]
        cls.package_type_company_1 = cls.package_type_obj.create(
            {"name": "Box Company 1", "company_ids": [(6, 0, cls.company_1.ids)]}
        )
        cls.package_type_company_2 = cls.package_type_obj.create(
            {"name": "Box Company 2", "company_ids": [(6, 0, cls.company_2.ids)]}
        )
        cls.package_type_no_company = cls.package_type_obj.create(
            {"name": "Box no company", "company_ids": []}
        )

    @classmethod
    def _create_packaging(cls):
        cls.packaging_obj = cls.env["product.packaging"]

        cls.packaging_company_1 = cls.packaging_obj.with_company(cls.company_1).create(
            {
                "name": "Packaging Company 1",
                "product_id": cls.product_company_1.id,
                "company_ids": [(6, 0, cls.company_1.ids)],
                "package_type_id": cls.package_type_company_1.id,
            }
        )

        cls.packaging_company_2 = cls.packaging_obj.with_company(cls.company_2).create(
            {
                "name": "Packaging Company 2",
                "product_id": cls.product_company_2.id,
                "company_ids": [(6, 0, cls.company_2.ids)],
                "package_type_id": cls.package_type_company_2.id,
            }
        )

        cls.packaging_company_both = cls.packaging_obj.create(
            {
                "name": "Packaging both",
                "product_id": cls.product_company_1.id,
                "company_ids": [(6, 0, (cls.company_1 + cls.company_2).ids)],
                "package_type_id": cls.package_type_company_1.id,
            }
        )

        cls.packaging_no_company = cls.packaging_obj.create(
            {
                "name": "Packaging no company",
                "product_id": cls.product_no_company.id,
                "company_ids": [],
                "company_id": False,
                "package_type_id": cls.package_type_no_company.id,
            }
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.groups = cls.env.ref("base.group_system")
        cls._create_companies()
        cls._create_users()
        cls._create_products()
        cls._create_package_types()
        cls._create_packaging()
