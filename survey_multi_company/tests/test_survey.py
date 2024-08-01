# Copyright 2023- Le Filament (https://le-filament.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.tests.common import TransactionCase, tagged


@tagged("survey_multi_company")
class TestSurveyMultiCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company1 = cls.env.ref("base.main_company")
        cls.company2 = cls.env["res.company"].create(
            {
                "name": "company 2",
            }
        )
        cls.user1 = cls.env.ref("base.user_admin")
        cls.user2 = cls.user1.copy(
            {
                "company_id": cls.company2.id,
                "company_ids": [(6, 0, [cls.company2.id])],
            }
        )

        cls.survey = cls.env["survey.survey"]

        cls.survey_1 = cls.survey.create(
            {
                "title": "one",
                "company_id": cls.company1.id,
            }
        )
        cls.survey_2 = cls.survey.create(
            {
                "title": "two",
                "company_id": cls.company1.id,
            }
        )
        cls.survey_3 = cls.survey.create(
            {
                "title": "three",
                "company_id": cls.company2.id,
            }
        )

    def test_company_1_and_company_2(self):
        new_surveys = [self.survey_1.id, self.survey_2.id, self.survey_3.id]
        survey_list_1 = (
            self.env["survey.survey"]
            .with_user(self.user1.id)
            .search([("id", "in", new_surveys)])
        )
        self.assertEqual(len(survey_list_1), 2)

        survey_list_2 = (
            self.env["survey.survey"]
            .with_user(self.user2.id)
            .search([("id", "in", new_surveys)])
        )
        self.assertEqual(len(survey_list_2), 1)
