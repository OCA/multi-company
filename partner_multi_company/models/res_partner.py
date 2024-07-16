# Copyright 2015 Oihane Crucelaegui
# Copyright 2015-2019 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html.html

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = ["multi.company.abstract", "res.partner"]
    _name = "res.partner"

    # This is needed because after installation this field becomes
    # unsearchable and unsortable. Which is not explicitly changed in this
    # module and as such can be considered an undesired yield.
    display_name = fields.Char(
        compute="_compute_display_name",
        store=True,
        index=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Neutralize the default value applied to company_id that can't be
        removed in the inheritance, and that will activate the inverse method,
        overwriting our company_ids field desired value.
        """
        for vals in vals_list:
            self._amend_company_id(vals)
        return super().create(vals_list)

    @api.model
    def _commercial_fields(self):
        """Add company_ids to the commercial fields that will be synced with
         childs. Ideal would be that this field is isolated from company field,
         but it involves a lot of development (default value, incoherences
         parent/child...).
        :return: List of field names to be synced.
        """
        commercial_fields = super()._commercial_fields()
        commercial_fields += ["company_ids"]
        return commercial_fields

    @api.model
    def _amend_company_id(self, vals):
        if "company_ids" in vals:
            if not vals["company_ids"]:
                vals["company_id"] = False
            else:
                for item in vals["company_ids"]:
                    if item[0] in (Command.UPDATE, Command.LINK):
                        vals["company_id"] = item[1]
                    elif item[0] in (Command.DELETE, Command.UNLINK, Command.CLEAR):
                        vals["company_id"] = False
                    elif item[0] == Command.SET:
                        if item[2]:
                            vals["company_id"] = item[2][0]
                        else:  # pragma: no cover
                            vals["company_id"] = False
        elif "company_id" not in vals:
            vals["company_ids"] = False
        return vals

    @api.constrains("company_ids")
    def _check_company_id(self):
        for rec in self:
            if rec.user_ids:
                user_company_ids = set(rec.user_ids.mapped("company_ids").ids)
                partner_company_ids = set(rec.company_ids.ids)

                if (
                    not user_company_ids.issubset(partner_company_ids)
                    and partner_company_ids
                ):
                    raise ValidationError(
                        _(
                            "The partner must have at least all the companies "
                            "associated with the user."
                        )
                    )

    def _inverse_company_id(self):
        if self.env.context.get("from_res_users"):
            # don't delete all partner company_ids when
            # the user's related company_id is modified.
            for record in self:
                company = record.company_id
                if company:
                    record.company_ids = [Command.link(company.id)]
            return
        else:
            return super()._inverse_company_id()
