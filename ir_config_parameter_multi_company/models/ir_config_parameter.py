from odoo import api, fields, models
from odoo.osv import expression


class IrConfigMultiCompany(models.Model):
    _inherit = "ir.config_parameter"
    company_id = fields.Many2one("res.company", "Company")

    _sql_constraints = [
        ("key_uniq", "unique (key, company_id)", "Key must be unique per company.")
    ]

    # this is needed because get_param is usually called with sudo
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if count:
            return super().search(args, offset, limit, order, count)
        key_present = False
        for item in args:
            if len(item) == 3 and item[0] == "key":
                key_present = True
        if not key_present:
            return super().search(args, offset, limit, order, count)
        else:
            # avoid limit to fetch all values
            records = super().search(
                args=args, offset=offset, limit=None, order=order, count=count
            )
            if len(records) > 1:
                # key must be unique per company
                args = expression.AND(
                    (args, [("company_id", "=", self.env.company.id)])
                )
                records = super().search(
                    args=args, offset=offset, limit=None, order=order, count=count
                )
                if len(records) > 1:
                    # call with limit
                    records = super().search(
                        args=args, offset=offset, limit=limit, order=order, count=count
                    )
        return records

    @api.model
    def _get_param(self, key):
        # because self.env.company.id is not in cache key
        self.clear_caches()
        return super()._get_param(key)
