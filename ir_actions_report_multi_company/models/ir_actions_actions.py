# Copyright 2022 XCG Consulting
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, tools


class IrActions(models.Model):
    _inherit = "ir.actions.actions"

    # Add companies to the cache of this method that is used in
    # models.BaseModels.fields_view_get to get the toolbar actions that are now
    # company dependant.
    @api.model
    @tools.ormcache(
        "frozenset(self.env.user.groups_id.ids)",
        "frozenset(self.env.companies.ids)",
        "model_name",
    )
    def get_bindings(self, model_name):
        """Retrieve the list of actions bound to the given model.

        :return: a dict mapping binding types to a list of dict describing
                 actions, where the latter is given by calling the method
                 ``read`` on the action record.
        """
        # Using __wrapped__ is necessary to bypass the cache put by Odoo on the
        # super method.
        result = super().get_bindings.__wrapped__(self, model_name)
        return result
