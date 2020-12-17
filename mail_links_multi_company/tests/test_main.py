from odoo.tests.common import TransactionCase
from urllib.parse import urlparse
import re


class TestMain(TransactionCase):
    def setUp(self):
        super().setUp()
        self.test_partner = self.env.ref("base.res_partner_1")
        self.test_company = self.env.ref("base.main_company")
        self.test_company.web_base_url_mail = "https://foo.bar"
        self.env["ir.config_parameter"].set_param(
            "web.base.url", "http://localhost:8069"
        )

    def test_notify_followers_html(self):
        """Test scenario that simulates notification
        sent to new followers (like in thread._message_auto_subscribe_notify())
        """
        record = self.test_partner
        view = self.env["ir.ui.view"].browse(
            self.env["ir.model.data"].xmlid_to_res_id(
                "mail.message_user_assigned"
            )
        )
        model_description = (
            self.env["ir.model"]._get(record._name).display_name
        )
        values = {
            "object": record,
            "model_description": model_description,
        }
        html = view.render(values, engine="ir.qweb", minimal_qcontext=True)

        # Test with company not set
        record.company_id = False
        new_html = self.env["mail.thread"]._replace_local_links(html)
        urls = re.findall(r'href=[\'"]?([^\'" >]+)', new_html)
        self.assertEqual(len(urls), 1)
        self.assertEqual(urlparse(urls[0]).scheme, "http")
        self.assertEqual(urlparse(urls[0]).netloc, "localhost:8069")

        # Test with company set
        record.company_id = self.test_company
        new_html = self.env["mail.thread"]._replace_local_links(html)
        urls = re.findall(r'href=[\'"]?([^\'" >]+)', new_html)
        self.assertEqual(len(urls), 1)
        self.assertEqual(urlparse(urls[0]).scheme, "https")
        self.assertEqual(urlparse(urls[0]).netloc, "foo.bar")
