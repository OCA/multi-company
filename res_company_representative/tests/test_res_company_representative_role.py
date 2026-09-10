# Copyright (C) 2026-TODAY NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
# @author Nils Coenen <nils.coenen@nico-solutions.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from psycopg2 import IntegrityError

from odoo.tests import TransactionCase


class TestResCompanyRepresentativeRole(TransactionCase):
    def test_role_name_must_be_unique(self):
        self.env["res.company.representative.role"].create(
            {
                "name": "Owner",
            }
        )

        logger = logging.getLogger("odoo.sql_db")
        previous_level = logger.level
        logger.setLevel(logging.CRITICAL)

        try:
            with self.assertRaises(IntegrityError), self.env.cr.savepoint():
                self.env["res.company.representative.role"].create(
                    {
                        "name": "Owner",
                    }
                )
        finally:
            logger.setLevel(previous_level)
