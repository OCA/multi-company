# Copyright 2026 XXP LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.http import _request_stack

from odoo.addons.base.tests.common import BaseCommon

from .common import SingleActiveCompanyCommon


class _Session:
    def __init__(self, uid):
        self.uid = uid
        self.context = {"lang": "en_US"}
        self.debug = ""
        self.profile_session = False
        self.profile_collectors = False
        self.profile_params = False


class _Request:
    def __init__(self, env):
        self.session = _Session(env.uid)
        self.env = env
        self.db = False


class TestResUsersSingleActiveCompany(SingleActiveCompanyCommon, BaseCommon):
    def _session_info(self, user):
        """Call session_info with a bound request.

        Several ir.http overrides read odoo.http.request. That proxy is empty
        in TransactionCase, so push a request for the duration of the call.
        """
        user_env = self.env(user=user.id)
        req = _Request(user_env)
        _request_stack.push(req)
        try:
            return user_env["ir.http"].session_info()
        finally:
            if _request_stack.top is req:
                _request_stack.pop()

    def test_group_implies_multi_company(self):
        """The group sits with Multi Companies and implies that group."""
        user = self._create_user(
            "sac_implied",
            [self.company_a, self.company_b],
            single_active_company=True,
            groups=self.group_user,
        )
        self.assertTrue(
            user.has_group(
                "res_users_single_active_company.group_single_active_company"
            )
        )
        self.assertTrue(user.has_group("base.group_multi_company"))

    def test_limit_requires_multi_company_group(self):
        """Single Active Company does nothing without Multi Companies."""
        self.env.cr.execute(
            """
            DELETE FROM res_groups_users_rel
            WHERE uid = %s AND gid = %s
            """,
            (self.user.id, self.group_multi_company.id),
        )
        self.env.registry.clear_caches()
        self.assertTrue(
            self.user.has_group(
                "res_users_single_active_company.group_single_active_company"
            )
        )
        self.assertFalse(self.user.has_group("base.group_multi_company"))
        self.assertFalse(self.user._single_active_company_limit_active())
        info = self._session_info(self.user)
        self.assertFalse(info["allow_single_company"])

    def test_group_keeps_allowed_companies(self):
        """Membership does not shrink the allowed company list."""
        self.assertTrue(
            self.user.has_group(
                "res_users_single_active_company.group_single_active_company"
            )
        )
        self.assertEqual(
            set(self.user.company_ids.ids),
            {self.company_a.id, self.company_b.id},
        )

    def test_session_info_flag_true(self):
        """session_info is set when the user has the group."""
        info = self._session_info(self.user)
        self.assertTrue(info["allow_single_company"])

    def test_session_info_flag_false(self):
        """session_info is unset when the user does not have the group."""
        info = self._session_info(self.user_plain)
        self.assertFalse(info["allow_single_company"])

    def test_apply_allowed_company_keeps_allowed_companies(self):
        """Applying an allowed company keeps the allowed companies."""
        user = self.user.with_user(self.user)
        allowed_ids = set(user.company_ids.ids)
        self.assertTrue(user._apply_single_active_company(self.company_b))
        self.assertEqual(user.company_id, self.company_b)
        self.assertEqual(set(user.company_ids.ids), allowed_ids)

    def test_public_method_accepts_company_id(self):
        """The public method accepts a company id."""
        user = self.user.with_user(self.user)
        self.assertTrue(user.apply_single_active_company(self.company_a.id))
        self.assertEqual(user.company_id, self.company_a)
        self.assertEqual(
            set(user.company_ids.ids),
            {self.company_a.id, self.company_b.id},
        )

    def test_apply_company_outside_allowed_raises(self):
        """A company outside the allowed list raises an error."""
        other_company = self.env["res.company"].create({"name": "SAC Company C"})
        user = self.user.with_user(self.user)
        with self.assertRaises(UserError) as error:
            user._apply_single_active_company(other_company)
        self.assertEqual(error.exception.args[0], "Select an allowed company.")

    def test_apply_without_group_raises(self):
        """Applying a company without the group raises an error."""
        user = self.user_plain.with_user(self.user_plain)
        with self.assertRaises(UserError) as error:
            user._apply_single_active_company(self.company_a)
        self.assertEqual(
            error.exception.args[0],
            "Single Active Company is not enabled for this user.",
        )
