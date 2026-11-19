# Copyright 2026 Quentin DUPONT
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import UserError
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestPosUnlinkPartnerMultiCompany(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestPosUnlinkPartnerMultiCompany, cls).setUpClass()
        # Avoid possible spam
        cls.partner_model = cls.env["res.partner"].with_context(
            mail_create_nosubscribe=True,
        )
        cls.company_1_with_pos = cls.env.ref("base.main_company")
        cls.partner_company_none = cls.partner_model.create(
            {"name": "partner without company", "company_id": False}
        )
        cls.partner_1_company_1 = cls.partner_model.create(
            {
                "name": "partner from company 1",
                "company_id": cls.company_1_with_pos.id,
            }
        )
        cls.partner_2_company_1 = cls.partner_model.create(
            {
                "name": "partner from company 1",
                "company_id": cls.company_1_with_pos.id,
            }
        )

    def test_001_unlink_partner(self):
        # No Error
        self.partner_1_company_1._unlink_except_active_pos_session()
        # Open pos session for company 1
        self.pos_config = self.env.ref("point_of_sale.pos_config_main")
        self.pos_config.open_ui()
        self.session = self.pos_config.current_session_id

        # Error for partner of company 1
        with self.assertRaises(UserError):
            self.partner_2_company_1._unlink_except_active_pos_session()

        # Error for partner withour company
        with self.assertRaises(UserError):
            self.partner_company_none._unlink_except_active_pos_session()
