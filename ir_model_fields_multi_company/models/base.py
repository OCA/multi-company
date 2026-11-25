from odoo import _, models
from odoo.exceptions import UserError

# Service fields that Odoo may put into `vals` itself; they must never
# trigger the multi-company restriction.
TECHNICAL_FIELDS = frozenset(
    models.MAGIC_COLUMNS + ["parent_path", models.BaseModel.CONCURRENCY_CHECK_FIELD]
)


class Base(models.AbstractModel):
    _inherit = "base"

    def write(self, vals):
        # Enforce the field-level multi-company restriction only for regular
        # users on models that carry a company_id field; superuser writes
        # (env.su) are never restricted.
        if not self.env.su and "company_id" in self._fields:
            self._check_allow_multi_company_write(vals)
        return super().write(vals)

    def _check_allow_multi_company_write(self, vals):
        """Restrict writes on other companies' records to allowed fields.

        When at least one field of the model is flagged with
        ``allow_multi_company_write``, only flagged fields may be changed on
        records whose company is not among ``self.env.companies``. Raise a
        ``UserError`` listing the fields that are not allowed for editing.
        """
        field_names = set(vals) - TECHNICAL_FIELDS
        if not field_names:
            return
        companies = self.env.companies
        foreign_records = self.filtered(
            lambda rec: rec.company_id and rec.company_id not in companies
        )
        if not foreign_records:
            return
        # Regular users have no read access to ir.model.fields.
        model_fields = self.env["ir.model.fields"].sudo()
        allowed_fields = model_fields.search(
            [
                ("model", "=", self._name),
                ("allow_multi_company_write", "=", True),
            ]
        )
        if not allowed_fields:
            # No whitelist defined on the model: keep standard behavior.
            return
        forbidden_names = field_names - set(allowed_fields.mapped("name"))
        if not forbidden_names:
            return
        forbidden_fields = model_fields.search(
            [("model", "=", self._name), ("name", "in", list(forbidden_names))]
        )
        labels = forbidden_fields.mapped("field_description")
        labels += list(forbidden_names - set(forbidden_fields.mapped("name")))
        raise UserError(
            _(
                "The following fields are not allowed for editing "
                "on another company's record: %s",
                ", ".join(sorted(labels)),
            )
        )
