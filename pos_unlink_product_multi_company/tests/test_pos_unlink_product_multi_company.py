# Copyright 2026 Quentin DUPONT
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import UserError
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestProductUnlinkPartnerMultiCompany(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestProductUnlinkPartnerMultiCompany, cls).setUpClass()
        cls.partner = cls.env.ref("base.res_partner_1")
        cls.user = cls.env.ref("base.user_admin")
        cls.product_p = cls.env.ref("product.product_product_4")
        cls.product_t = cls.env.ref("product.product_product_25_product_template")
        cls.pos_config = cls.env.ref("point_of_sale.pos_config_main")

    def test_001_unlink_product_product(self):
        # No Error
        self.product_p._unlink_except_active_pos_session()

        # Error
        self.pos_config.open_ui()
        with self.assertRaises(UserError):
            self.product_p._unlink_except_active_pos_session()

    def test_002_unlink_product_template(self):
        # No Error
        self.product_t._unlink_except_open_session()

        # Error
        self.pos_config.open_ui()
        with self.assertRaises(UserError):
            self.product_t._unlink_except_open_session()
