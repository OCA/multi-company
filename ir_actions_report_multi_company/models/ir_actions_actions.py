# Copyright 2022 XCG Consulting
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, tools
from odoo.tools import frozendict


class IrActionsActions(models.Model):
    _inherit = "ir.actions.actions"

    # Add companies to the cache of this method that is used in
    # models.BaseModels.fields_view_get to get the toolbar actions that are now
    # company dependant.
    @tools.ormcache(
        "frozenset(self.env.user.groups_id.ids)",
        "frozenset(self.env.companies.ids)",
        "model_name",
        "self.env.lang",
    )
    def _get_bindings(self, model_name):
        """Retrieve the list of actions bound to the given model.

        :return: a dict mapping binding types to a list of dict describing
                 actions, where the latter is given by calling the method
                 ``read`` on the action record.
        """
        # get company related reports
        reports = self._get_report_bindings(model_name)

        # Using __wrapped__ is necessary to bypass the cache put by Odoo on the
        # super method.
        result = super()._get_bindings.__wrapped__(self, model_name)

        # update bindings result
        if reports:
            result = dict(result)
            result["report"] = reports
            result = frozendict(result)

        return result

    def _get_report_bindings(self, model_name):
        """
        Get report bindings for current company
        """
        cr = self.env.cr
        self.env.flush_all()

        query = """
            SELECT report.id, report.type
              FROM ir_act_report_xml report
              JOIN ir_model m ON report.binding_model_id = m.id
             WHERE m.model = %s
               AND (report.company_id = ANY(%s) OR report.company_id IS NULL)
               AND report.binding_type = 'report'
        """
        cr.execute(query, (model_name, self.env.companies.ids))

        report_ids = [report_id for report_id, report_type_ in cr.fetchall()]
        result = []

        if report_ids:
            reports = (
                self.env["ir.actions.report"]
                .sudo()
                .search_read(
                    [("id", "in", report_ids)],
                    ["name", "binding_view_types", "groups_id", "model"],
                    order="id",
                )
            )

            groups_obj = self.env["res.groups"]
            model_access_obj = self.env["ir.model.access"]

            for report in reports:
                group_ids = report.pop("groups_id", None)
                if group_ids:
                    groups = groups_obj.browse(group_ids)
                    xml_ids = ",".join(
                        ext_id for ext_id in groups._ensure_xml_id().values()
                    )
                    if groups and not self.user_has_groups(xml_ids):
                        # the user may not perform this action
                        continue

                model = report.pop("model", None)
                if model and not model_access_obj.check(
                    model, mode="read", raise_exception=False
                ):
                    # the user won't be able to read records
                    continue

                result.append(frozendict(report))

        return result
