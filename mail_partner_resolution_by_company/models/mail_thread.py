# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv import expression


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model
    def _mail_find_partner_from_emails(
        self, emails, records=None, force_create=False, extra_domain=False
    ):
        company_ids = []
        if records and "company_id" in records._fields:
            company_ids = records.mapped("company_id").ids
        if not company_ids:
            company_ids = [self.env.company.id]
        extra_domain = expression.AND(
            [extra_domain or [], [("company_id", "in", company_ids + [False])]]
        )
        return super()._mail_find_partner_from_emails(
            emails,
            records=records,
            force_create=force_create,
            extra_domain=extra_domain,
        )
