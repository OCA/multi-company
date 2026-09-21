# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import config


class MultiCompanyAbstract(models.AbstractModel):
    _inherit = "multi.company.abstract"

    # Display proxy over ``company_ids`` meant for a *non* multi-company user (a
    # merchant). It only ever exposes the companies that user owns, so the real
    # ``company_ids`` -- which may also point to other companies (shared or
    # global records) -- never reaches them. Editable, with a safe merge.
    own_company_ids = fields.Many2many(
        comodel_name="res.company",
        # Unique technical label to avoid clashing with ``company_id``; the
        # user-facing label ("Company") is set on the field in the views.
        string="Own Company",
        compute="_compute_own_company_ids",
        inverse="_inverse_own_company_ids",
        search="_search_own_company_ids",
        # The value depends on *who* reads it (each user owns a different set of
        # companies), so it must not be shared across users in the cache.
        depends_context=("uid",),
    )
    # Drives the view visibility (``invisible="not show_own_company_field"``):
    # only ON for a non multi-company user when the model is enabled in settings.
    show_own_company_field = fields.Boolean(
        compute="_compute_show_own_company_field",
        # Depends on *who* reads it (their group and the per-model setting), so
        # the result must not be shared across users in the cache.
        compute_sudo=False,
        depends_context=("uid",),
    )

    @api.depends("company_ids")
    def _compute_own_company_ids(self):
        for record in self:
            if not record._show_own_company_field_enabled():
                # Nobody reads this proxy when the real field is shown
                # instead (multi-company users) or the model's toggle is
                # off, so skip it entirely. Setting a Many2many field --
                # even to fill a compute's cache -- goes through the same
                # write path as a real edit, which checks 'read' access on
                # any newly-referenced res.company; since this field's
                # value is scoped to `self.env.user.company_ids` (every
                # company the user belongs to) rather than
                # `self.env.companies` (only the ones active in the
                # company switcher right now), a multi-company user who
                # narrowed their active selection would otherwise trip
                # that check on a company they own but didn't select.
                record.own_company_ids = False
                continue
            # ``sudo`` reads the raw m2m without tripping over res.company rules;
            # the result is already narrowed to the user's own companies, so
            # nothing foreign is ever revealed.
            own = self.env.user.company_ids
            record.own_company_ids = record.sudo().company_ids & own

    def _inverse_own_company_ids(self):
        own = self.env.user.company_ids
        for record in self:
            stored = record.sudo().company_ids
            # Companies the user cannot see stay untouched (merge, no leak/wipe).
            hidden = stored - own
            # Only accept companies the user actually owns; a merchant may pick
            # one, several or all of them, but never a foreign one.
            chosen = record.own_company_ids & own
            # Never blank: fall back to the user's current company.
            if not chosen:
                chosen = self.env.company
            record.sudo().company_ids = [Command.set((hidden | chosen).ids)]

    def _search_own_company_ids(self, operator, value):
        # Mirror a search on the proxy onto the real field, scoped to the
        # user's own companies so it can never surface foreign records.
        own = self.env.user.company_ids
        return [
            "&",
            ("company_ids", operator, value),
            ("company_ids", "in", own.ids),
        ]

    def _compute_show_own_company_field(self):
        show = self._show_own_company_field_enabled()
        for record in self:
            record.show_own_company_field = show

    @api.model
    def _show_own_company_field_enabled(self):
        # Multi-company users already have the full ``company_ids`` field gated
        # by ``base.group_multi_company``; the proxy is only for the others.
        if self.env.user.has_group("base.group_multi_company"):
            return False
        return self._own_company_field_param_enabled()

    @api.model
    def _own_company_field_param_enabled(self):
        """Whether the per-model settings toggle is on. Enabled by default."""
        key = self._own_company_field_param_key()
        if not key:
            # The abstract model has no concrete key; each bridge overrides
            # ``_own_company_field_param_key`` for its model.
            return False
        param = self.env["ir.config_parameter"].sudo().get_param(key, "True")
        return param not in ("False", "false", "0", "")

    @api.model
    def _own_company_field_param_key(self):
        """``ir.config_parameter`` key gating this model. Bridges override it."""
        return None

    def _check_own_company_not_blank(self):
        # Safety net behind the inverse: a non multi-company user must not end
        # up with a blank (global) company set on an exposed model.
        #
        # This is deliberately NOT an ``@api.constrains``: while ``write()``
        # holds ``company_ids`` protected (it feeds the computed
        # ``company_id``), ``record.sudo().company_ids`` still reads the
        # *pre-write* value, so a constrain would silently pass on the very
        # write that empties it. Called instead from ``create``/``write``
        # below, once the ORM call has fully returned and the field is
        # readable again.
        if config["test_enable"] and not self.env.context.get(
            "test_multi_company_field_visible"
        ):
            return
        if self.env.context.get("default_parent_id") is False:
            # Core's own ``res.company.create()`` creates a brand new
            # company's own contact through exactly this context marker
            # (``odoo/addons/base/models/res_company.py``, the "create
            # missing partners" block). At that point in the ORM's create
            # flow, ``base_multi_company``'s ``_inverse_company_id`` fires
            # as a side effect and briefly clears ``company_ids`` (its
            # source, ``company_id``, has nothing to compute from yet:
            # the company doesn't have ``partner_id`` set back to this
            # very partner until a moment later). This transient, internal
            # empty state is not a real user-facing edit, so it must not
            # be rejected here; whatever consuming module scopes a
            # company's own contact to itself (e.g.
            # ``partner_multi_company_restrict``) fixes it up right after.
            return
        if self.env.user.has_group("base.group_multi_company"):
            # Admins may leave it empty on purpose ("All companies" / global).
            return
        for record in self:
            if not record._own_company_field_param_enabled():
                continue
            record.invalidate_recordset(["company_ids"])
            if not record.sudo().company_ids:
                raise ValidationError(
                    self.env._(
                        "You must assign at least your own company to “%(name)s”.",
                        name=record.display_name,
                    )
                )

    def write(self, vals):
        result = super().write(vals)
        if "company_ids" in vals:
            self._check_own_company_not_blank()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_own_company_not_blank()
        return records
