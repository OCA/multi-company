# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
from odoo import fields, models


class IrModelFields(models.Model):
    _inherit = "ir.model.fields"

    allow_multi_company_write = fields.Boolean(
        string="Allow Multi-Company Write",
        default=False,
        help="If enabled, this field can be edited on another company's records.",
    )

    def write(self, vals):
        # The standard write() forbids altering base (non-manual) fields, but
        # the flag does not affect the field definition, so it is safe to
        # change on any field. Write it separately, bypassing that
        # restriction; core does the same for website_form_blacklisted
        # (see odoo/addons/website/models/website_form.py).
        if "allow_multi_company_write" in vals:
            vals = dict(vals)
            value = vals.pop("allow_multi_company_write")
            self.check_access_rights("write")
            self.check_access_rule("write")
            self._write({"allow_multi_company_write": value})
            self.invalidate_recordset(["allow_multi_company_write"])
        if not vals:
            return True
        return super().write(vals)
