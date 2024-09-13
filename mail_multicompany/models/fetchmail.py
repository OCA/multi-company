# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class FetchmailServer(models.Model):

    _inherit = "fetchmail.server"

    company_id = fields.Many2one("res.company", "Company")
