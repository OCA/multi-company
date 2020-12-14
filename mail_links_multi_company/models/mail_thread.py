from odoo import models
from urllib.parse import urlparse, parse_qs
import re


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _replace_local_links(self, html, base_url=None):
        if not base_url:
            urls = re.findall(r'href=[\'"]?([^\'" >]+)', html)
            for url in urls:
                query = parse_qs(urlparse(url).query)
                model = query.get("model", [""])[0]
                res_id = query.get("res_id", [""])[0]
                if model and res_id.isdigit():
                    rec = self.env[model].browse(int(res_id))
                    if (
                        hasattr(rec, "company_id")
                        and rec.company_id.web_base_url_mail
                    ):
                        base_url = rec.company_id.web_base_url_mail
                        break
        return super()._replace_local_links(html, base_url=base_url)
