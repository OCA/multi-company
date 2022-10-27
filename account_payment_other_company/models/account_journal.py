# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
    ):
        context = self._context or {}
        others_companies = (
            self.env["res.company"]
            .with_user(SUPERUSER_ID)
            .search([("id", "<>", self.env.company.id)])
        )
        if context.get("sudo"):
            args += [
                ("type", "in", ("bank", "cash")),
                ("company_id", "<>", self.env.company.id),
                (
                    "id",
                    "not in",
                    others_companies.mapped("due_fromto_payment_journal_id").ids,
                ),
            ]
            return super(AccountJournal, self.with_user(SUPERUSER_ID))._search(
                args,
                offset,
                limit,
                order,
                count=count,
                access_rights_uid=access_rights_uid,
            )
        return super()._search(
            args, offset, limit, order, count=count, access_rights_uid=access_rights_uid
        )

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.context.get("sudo", False):
            records = self.with_user(SUPERUSER_ID).search(
                domain or [], offset=offset, limit=limit, order=order
            )
        else:
            records = self.search(domain or [], offset=offset, limit=limit, order=order)

        if not records:
            return []

        if fields and fields == ["id"]:
            # shortcut read if we only want the ids
            return [{"id": record.id} for record in records]
        if "active_test" in self._context:
            context = dict(self._context)
            del context["active_test"]
            records = records.with_context(context)

        result = records.read(fields)
        if len(result) <= 1:
            return result

        # reorder read
        index = {vals["id"]: vals for vals in result}
        return [index[record.id] for record in records if record.id in index]

    def name_get(self):
        res = []
        for journal in self.with_user(SUPERUSER_ID):
            name = journal.name
            if (
                journal.currency_id
                and journal.currency_id != journal.company_id.currency_id
            ):
                name = "%s (%s)" % (name, journal.currency_id.name)
            res += [(journal.id, name)]
        return res
