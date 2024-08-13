import json
from uuid import uuid4

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestSessionInfo(HttpCase):
    def test_admin_user(self):
        self.authenticate("admin", "admin")
        info = self._get_session_info()
        self.assertGreater(len(info["user_companies"]["allowed_companies"]), 1)

    def test_portal_user(self):
        self.authenticate("portal", "portal")
        info = self._get_session_info()
        self.assertNotIn("user_companies", info)

    def _get_session_info(self):
        data = json.dumps(dict(jsonrpc="2.0", method="call", id=str(uuid4())))
        headers = {"Content-Type": "application/json"}
        response = self.url_open(
            "/web/session/get_session_info", data=data, headers=headers
        )
        return response.json()["result"]
