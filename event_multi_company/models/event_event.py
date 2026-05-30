# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class EventEvent(models.Model):
    _inherit = ["multi.company.abstract", "event.event"]
    _name = "event.event"
