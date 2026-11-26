# Copyright 2026 XXP LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
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

    def test_default_flag_is_false(self):
        user = self.env["res.users"].create(
            {
                "name": "SAC Default User",
                "login": "sac_default_user",
                "email": "sac_default_user@example.com",
                "groups_id": [Command.set([self.group_user.id])],
            }
        )
        self.assertFalse(user.allow_single_company)

    def test_flag_keeps_allowed_companies(self):
        """
        Test that the flag keeps the allowed companies.
        """
        self.user.allow_single_company = True
        self.assertTrue(
            self.user.allow_single_company, "Allow Single Company is not set"
        )
        self.assertEqual(
            set(self.user.company_ids.ids),
            {self.company_a.id, self.company_b.id},
            "Allowed companies are not kept",
        )

    def test_session_info_flag_true(self):
        """
        Test that the Allow Single Company field is set
        when the user has the Multi Company group.
        """
        info = self._session_info(self.user)
        self.assertTrue(
            info["allow_single_company"],
            "Allow Single Company is not set",
        )

    def test_session_info_flag_false(self):
        """
        Test that the Allow Single Company field is not set
        when the user does not have the Multi Company group.
        """
        info = self._session_info(self.user_plain)
        self.assertFalse(
            info["allow_single_company"],
            "Allow Single Company is not set",
        )

    def test_session_info_without_multi_company_group(self):
        """
        Test that the Allow Single Company field is not set
        when the user does not have the Multi Company group.
        """
        self.assertTrue(
            self.user_single.allow_single_company,
            "Allow Single Company is not set",
        )
        info = self._session_info(self.user_single)
        self.assertFalse(
            info["allow_single_company"],
            "Allow Single Company is not set",
        )

    def test_apply_allowed_company_keeps_allowed_companies(self):
        """
        Test that applying an allowed company keeps the allowed companies.
        """
        user = self.user.with_user(self.user)
        allowed_ids = set(user.company_ids.ids)
        self.assertTrue(
            user._apply_single_active_company(self.company_b),
            "Company is not applied",
        )
        self.assertEqual(
            user.company_id,
            self.company_b,
            "Company is not set",
        )
        self.assertEqual(
            set(user.company_ids.ids),
            allowed_ids,
            "Allowed companies are not kept",
        )

    def test_public_method_accepts_company_id(self):
        """
        Test that the public method accepts a company id.
        """
        user = self.user.with_user(self.user)
        self.assertTrue(
            user.apply_single_active_company(self.company_a.id),
            "Company is not applied",
        )
        self.assertEqual(
            user.company_id,
            self.company_a,
            "Company is not set",
        )
        self.assertEqual(
            set(user.company_ids.ids),
            {self.company_a.id, self.company_b.id},
            "Allowed companies are not kept",
        )

    def test_apply_company_outside_allowed_raises(self):
        """
        Test that applying a company outside the allowed companies raises an error.
        """
        other_company = self.env["res.company"].create({"name": "SAC Company C"})
        user = self.user.with_user(self.user)
        with self.assertRaises(UserError) as error:
            user._apply_single_active_company(other_company)
        self.assertEqual(
            error.exception.args[0],
            "Select an allowed company.",
            "Error message is not correct",
        )

    def test_apply_without_flag_raises(self):
        """
        Test that applying a company without the flag raises an error.
        """
        user = self.user_plain.with_user(self.user_plain)
        with self.assertRaises(UserError) as error:
            user._apply_single_active_company(self.company_a)
        self.assertEqual(
            error.exception.args[0],
            "Single Active Company is not enabled for this user.",
            "Error message is not correct",
        )
