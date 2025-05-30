from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class TestMailTemplateMultiCompany(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a company
        cls.company = cls.env["res.company"].create({"name": "Test Company"})

        # Create a user in the multi-company group
        cls.multi_company_user = cls.env["res.users"].create(
            {
                "name": "Multi Company User",
                "login": "multi_company_user",
                "email": "multi_company_user@example.com",
                "groups_id": [
                    (Command.set([cls.env.ref("base.group_multi_company").id]))
                ],
            }
        )

        # Create a mail template
        cls.mail_template = cls.env["mail.template"].create(
            {
                "name": "Test Template",
                "subject": "Test Subject",
                "company_id": cls.company.id,
            }
        )

    def test_company_id_field(self):
        """Test that the company_id field is correctly set and retrieved."""
        self.assertEqual(
            self.mail_template.company_id,
            self.company,
            "The company_id field should be correctly set in the mail template",
        )

    def test_field_visibility_in_views(self):
        """Test that the company_id field appears in views for multi-company users."""
        FormView = self.env.ref("mail_template_multi_company.mail_template_form_view")
        TreeView = self.env.ref("mail_template_multi_company.mail_template_tree_view")
        SearchView = self.env.ref(
            "mail_template_multi_company.mail_template_search_view"
        )

        # Simulate view rendering (pseudo-validation)
        self.assertTrue(
            "company_id" in FormView.arch,
            "The company_id field should appear in the form view for mail templates",
        )
        self.assertTrue(
            "company_id" in TreeView.arch,
            "The company_id field should appear in the tree view for mail templates",
        )
        self.assertTrue(
            "company_id" in SearchView.arch,
            "The company_id field should appear in the search view for mail templates",
        )

    def test_field_accessibility(self):
        # Create a user without access to the field
        restricted_user = self.env["res.users"].create(
            {
                "name": "Restricted User",
                "login": "restricted_user",
                "email": "restricted_user@example.com",
                "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )

        # Create a mail template as the restricted user
        mail_template = (
            self.env["mail.template"]
            .with_user(restricted_user)
            .create(
                {
                    "name": "Test Template",
                    "subject": "Test",
                    "body_html": "<p>Test Body</p>",
                }
            )
        )
        self.assertFalse(mail_template.company_id)

    def test_default_company_id(self):
        """Test that the company_id field defaults to False if not set."""
        template_without_company = self.env["mail.template"].create(
            {"name": "No Company Template"}
        )
        self.assertFalse(
            template_without_company.company_id,
            "The company_id field should be empty by default if not explicitly set",
        )
