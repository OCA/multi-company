# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.tests import HttpCase


class TestUi(HttpCase):

    def setUp(self):
        super(TestUi, self).setUp()

    def test_ui_web(self):
        """Test backend tests."""
        self.phantom_js(
            "/web/tests?module=web_responsive",
            "",
            login="admin",
        )
