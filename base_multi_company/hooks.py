# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2017 LasLabs Inc.
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html
from odoo import SUPERUSER_ID, _, api
from odoo.exceptions import UserError
from odoo.models import BaseModel

__all__ = [
    "post_init_hook",
    "uninstall_hook",
    "post_load",
]


def set_security_rule(env, rule_ref):
    """Set the condition for multi-company in the security rule.

    :param: env: Environment
    :param: rule_ref: XML-ID of the security rule to change.
    """
    rule = env.ref(rule_ref)
    if not rule:  # safeguard if it's deleted
        return
    rule.write(
        {
            "active": True,
            "domain_force": (
                "['|', ('no_company_ids', '=', True), ('company_ids', "
                "'in', company_ids)]"
            ),
        }
    )


def post_init_hook(cr, rule_ref, model_name):
    """Set the `domain_force` and default `company_ids` to `company_id`.

    Args:
        cr (Cursor): Database cursor to use for operation.
        rule_ref (string): XML ID of security rule to write the
            `domain_force` from.
        model_name (string): Name of Odoo model object to search for
            existing records.
    """
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        set_security_rule(env, rule_ref)
        # Copy company values
        model = env[model_name]
        table_name = model._fields["company_ids"].relation
        column1 = model._fields["company_ids"].column1
        column2 = model._fields["company_ids"].column2
        SQL = """
            INSERT INTO {}
            ({}, {})
            SELECT id, company_id FROM {} WHERE company_id IS NOT NULL
            ON CONFLICT DO NOTHING
        """.format(
            table_name,
            column1,
            column2,
            model._table,
        )
        env.cr.execute(SQL)


def uninstall_hook(cr, rule_ref):
    """Restore product rule to base value.

    Args:
        cr (Cursor): Database cursor to use for operation.
        rule_ref (string): XML ID of security rule to remove the
            `domain_force` from.
    """
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # Change access rule
        rule = env.ref(rule_ref)
        rule.write(
            {
                "active": False,
                "domain_force": (
                    " ['|', ('company_id', '=', user.company_id.id),"
                    " ('company_id', '=', False)]"
                ),
            }
        )


def post_load():  # noqa: C901
    def _check_company(self, fnames=None):
        """
        Monkey patch of 'BaseModel._check_company' to make it
        compatible with company_ids
        """
        if fnames is None:
            fnames = self._fields

        regular_fields = []
        property_fields = []
        for name in fnames:
            field = self._fields[name]
            if (
                field.relational
                and field.check_company
                and "company_id" in self.env[field.comodel_name]
            ):
                if not field.company_dependent:
                    regular_fields.append(name)
                else:
                    property_fields.append(name)

        if not (regular_fields or property_fields):
            return

        inconsistencies = []
        for record in self:
            if record._name == "res.company":
                company = record
            elif "company_ids" in record._fields:
                # if company_ids is present we use that
                company = record.company_ids
            else:
                # fallback on company_id
                company = record.company_id

            # if company is an empty recordset
            # we skip all the checks
            if company:
                for name in regular_fields:
                    corecord = record.sudo()[name]
                    if "company_ids" in corecord._fields and corecord.company_ids:
                        # Checks every field that belongs to multiple companies
                        # at least one company of record must also be in corecord companies
                        if not (company & corecord.company_ids):
                            inconsistencies.append((record, name, corecord))
                    elif not (corecord.company_id <= company):
                        # fallback on single company
                        inconsistencies.append((record, name, corecord))

            company = self.env.company
            for name in property_fields:
                corecord = record.sudo()[name]
                if "company_ids" in corecord._fields and corecord.company_ids:
                    # Checks every field that belongs to multiple companies
                    if not (company <= corecord.company_ids):
                        inconsistencies.append((record, name, corecord))
                elif not (corecord.company_id <= company):
                    inconsistencies.append((record, name, corecord))

        if inconsistencies:
            lines = [_("Incompatible companies on records:")]
            company_msg = _(
                "- Record is company %(company)r and %(field)r (%(fname)s: "
                "%(values)s) belongs to another company."
            )
            record_msg = _(
                "- %(record)r belongs to company %(company)r and %(field)r (%(fname)s: "
                "%(values)s) belongs to another company."
            )
            for record, name, corecords in inconsistencies[:5]:
                if record._name == "res.company":
                    msg, company = company_msg, record
                elif "company_ids" in record._fields:
                    msg, company = record_msg, record.company_ids
                else:
                    msg, company = record_msg, record.company_id
                field = self.env["ir.model.fields"]._get(self._name, name)
                lines.append(
                    msg
                    % {
                        "record": record.display_name,
                        "company": ",".join(company.mapped("display_name")),
                        "field": field.field_description,
                        "fname": field.name,
                        "values": ", ".join(
                            repr(rec.display_name) for rec in corecords
                        ),
                    }
                )
            raise UserError("\n".join(lines))

    BaseModel._patch_method("_check_company", _check_company)
