# Copyright 2026 Canarias Conectada
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, models
from odoo.tools import config


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model_create_multi
    def create(self, vals_list):
        # ``product_multi_company`` leaves new products global by default
        # (empty ``company_ids`` = visible to every company). For a strict
        # per-company setup that is the wrong default: a merchant creating a
        # product should get it scoped to its own company without having to
        # touch (or even see) the multi-company field.
        #
        # We set ``company_ids`` directly instead of defaulting ``company_id``:
        # ``company_id`` is a computed/inverse field here, and letting its
        # inverse run during ``create`` triggers an early write that the
        # company record rule rejects. Writing ``company_ids`` is the safe path.
        if not self._skip_company_default():
            company_command = Command.set(self.env.company.ids)
            multi_company_user = self.env.user.has_group("base.group_multi_company")
            for vals in vals_list:
                if vals.get("company_id") or self._commands_assign_companies(
                    vals.get("company_ids")
                ):
                    # An explicit company choice: respect it.
                    continue
                if "company_ids" in vals and multi_company_user:
                    # A deliberate global product (emptying commands, e.g.
                    # ``Command.set([])``), made by someone entitled to see
                    # and manage the multi-company field: respect it too.
                    continue
                # No company information -- or an emptying command sent by a
                # user the field is hidden from (only reachable through
                # RPC/imports, and it would make the product visible to
                # every company): scope to the active company.
                vals["company_ids"] = [company_command]
        return super().create(vals_list)

    @api.model
    def _commands_assign_companies(self, commands):
        """Whether a ``company_ids`` create() value yields at least one company.

        Plain truthiness is not enough: ``[Command.set([])]`` is a non-empty
        list that assigns no company at all.
        """
        if not isinstance(commands, list | tuple):
            return bool(commands)
        ids = set()
        for command in commands:
            if isinstance(command, list | tuple) and command:
                if command[0] == Command.SET:
                    ids = set(command[2] or [])
                elif command[0] in (Command.LINK, Command.UPDATE) and command[1]:
                    ids.add(command[1])
                elif command[0] == Command.CREATE:
                    return True
                elif command[0] == Command.CLEAR:
                    ids = set()
                elif command[0] in (Command.DELETE, Command.UNLINK):
                    ids.discard(command[1])
            elif isinstance(command, int) and command:
                ids.add(command)
        return bool(ids)

    @api.model
    def _skip_company_default(self):
        """Skip the default while a test suite runs (unless it opts in), so the
        global-by-default expectations of other modules keep passing."""
        return config["test_enable"] and not self.env.context.get(
            "test_product_company_default"
        )
