# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests.common import TransactionCase


class TestIrUiViewMultiCompany(TransactionCase):
    """
    The view `ir_ui_view_multi_company.ir_ui_view_form_view` extends
    `base.view_view_form`
    to include a `company_ids` field in the form view. In this test class we test
    ir.ui.view form view to see how the new field is displayed if we change the
    view company

    - The `company_ids` field is always visible if the view is not linked to any
      company.
    - If the view is linked to a specific company, it is only visible to users
      whose current company matches the view's company.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env.ref("base.user_admin")
        cls.company_1 = cls.env.company
        cls.company_2 = cls.env["res.company"].create({"name": "Company 2"})
        cls.user.company_ids += cls.company_2
        cls.view = cls.env.ref("ir_ui_view_multi_company.ir_ui_view_form_view")
        cls.view_model = cls.env["ir.ui.view"].with_user(cls.user)

    def _is_company_field_is_in_form_view(self, company):
        views = self.view_model.with_company(company).get_views([(False, "form")])
        arch = views["views"]["form"]["arch"]
        tree = etree.fromstring(arch.encode("utf-8"))
        return bool(tree.xpath('//field[@name="company_ids"]'))

    def test_0(self):
        """
        If the view is not linked to any company (shared view), the 'company_ids' field
        should be visible for users of all companies.
        """
        self.assertTrue(self._is_company_field_is_in_form_view(self.company_1))
        self.assertTrue(self._is_company_field_is_in_form_view(self.company_2))

    def test_1(self):
        """
        If the view is linked to company_2, it should not be visible to users when
        accessing it in the context of company_1.
        """
        self.view.company_ids = self.company_2
        self.assertFalse(self._is_company_field_is_in_form_view(self.company_1))

    def test_2(self):
        """
        If the view is linked to company_2, it should be visible to users when
        accessing it in the context of company_2.
        """
        self.view.company_ids = self.company_2
        self.assertTrue(self._is_company_field_is_in_form_view(self.company_2))

    def test_3(self):
        """
        If the view is linked to company_1 and company_2, it should be visible to
        users when accessing it in the context of both.
        """
        self.view.company_ids = self.company_1 + self.company_2
        self.assertTrue(self._is_company_field_is_in_form_view(self.company_1))
        self.assertTrue(self._is_company_field_is_in_form_view(self.company_2))
