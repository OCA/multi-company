# © 2023 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class FakeResPartner(models.Model):
    _name = "fake.res.partner"
    _description = "Test res partner"
    _inherit = "res.partner"

    phone = fields.Char(company_dependent=True)
    channel_ids = fields.Many2many(
        "discuss.channel",
        "fake_res_partner_mail_channel_rel",
        "partner_id",
        "channel_id",
    )
