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

    def test_replace_local_links(self):
        html = """
<p style="margin:0px">
    <span>Cher Foo Bar,</span><br>
    <span style="margin-top:8px">Lorem ipsum</span>
</p>
<p style="margin-top:24px; margin-bottom:16px">
    <a style="background-color:#875A7B; padding:10px; text-decoration:none;
color:#fff; border-radius:5px"
href="/mail/view?model=res.partner&amp;res_id={}">
            Lorem ipsum
    </a>
</p>
""".format(
            self.test_partner.id
        )
        self.test_partner.company_id = False
        new_html = self.env["mail.thread"]._replace_local_links(html)
        urls = re.findall(r'href=[\'"]?([^\'" >]+)', new_html)
        self.assertEqual(len(urls), 1)
        self.assertEqual(urlparse(urls[0]).scheme, "http")
        self.assertEqual(urlparse(urls[0]).netloc, "localhost:8069")
        self.test_partner.company_id = self.test_company
        new_html = self.env["mail.thread"]._replace_local_links(html)
        urls = re.findall(r'href=[\'"]?([^\'" >]+)', new_html)
        self.assertEqual(len(urls), 1)
        self.assertEqual(urlparse(urls[0]).scheme, "https")
        self.assertEqual(urlparse(urls[0]).netloc, "foo.bar")
