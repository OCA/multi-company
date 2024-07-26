# © 2014-2016 Akretion (http://www.akretion.com)
# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# @author: Quentin DUPONT
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    legal_name = fields.Char(
        help="Also called 'Business Name'.\n"
        "Set the official name of the company, and in the "
        "regular 'name' field, the Trade name of the company.",
    )

    legal_type = fields.Char(help="Type of Company, e.g. Ltd., SARL, GmbH ...")

    report_legal_description = fields.Char(
        compute="_compute_report_legal_description",
    )

    @api.depends("name", "legal_name", "legal_type")
    def _compute_report_legal_description(self):
        for company in self:
            name = company.legal_name or company.name
            if not company.legal_type:
                company.report_legal_description = name
            else:
                company.report_legal_description = _(f"{name}, {company.legal_type}")
