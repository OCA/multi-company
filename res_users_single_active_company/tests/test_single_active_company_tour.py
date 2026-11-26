# Copyright 2026 XXP LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import HttpCase

from .common import SingleActiveCompanyCommon


class TestSingleActiveCompanyTour(SingleActiveCompanyCommon, HttpCase):
    def test_single_active_company_tour(self):
        """
        Test the single active company tour.
        """
        url = "/web#cids=%s,%s" % (self.company_a.id, self.company_b.id)
        self.start_tour(
            url,
            "res_users_single_active_company.single_active_company",
            login=self.user.login,
        )
