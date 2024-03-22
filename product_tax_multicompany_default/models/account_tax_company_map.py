from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountTaxCompanyMap(models.Model):
    _name = "account.tax.company.map"
    _description = "Account Tax Company Map"

    name = fields.Char(string="Name", required=True, translate=True)
    tax_ids = fields.One2many("account.tax", "company_map_id")

    @api.constrains("tax_ids")
    def _check_tax_ids(self):
        for tax_map in self:
            for tax_type in tax_map.mapped("tax_ids.type_tax_use"):
                tax_ids = tax_map.tax_ids.filtered(lambda x: x.type_tax_use == tax_type)

                # Check that for every company there is only one tax
                company_ids = []
                for tax_id in tax_ids:
                    tax_company_id = tax_id.company_id
                    if tax_company_id in company_ids:
                        raise ValidationError(
                            _("Only one tax per company and type is allowed.")
                        )
                    else:
                        company_ids.append(tax_company_id)
