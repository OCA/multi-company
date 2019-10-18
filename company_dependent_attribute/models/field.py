# © 2019 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class IrModelFields(models.Model):
    _inherit = "ir.model.fields"

    company_dependent = fields.Boolean(
        compute="_compute_company_dependent", store=False
    )

    def _compute_company_dependent(self):
        for rec in self:
            rec.company_dependent = (
                self.env[rec.model]._fields[rec.name].company_dependent
            )
