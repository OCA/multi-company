from odoo.tests import TransactionCase


class TestCalendarEvent(TransactionCase):
    def test_default_company_id(self):
        event = self.env["calendar.event"].create(
            {
                "name": "NAME",
            }
        )
        self.assertEqual(event.company_id, self.env.company)
