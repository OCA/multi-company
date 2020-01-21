import odoo.tests.common as common


class TestAccountMove(common.TransactionCase):

    def setUp(self):
        super(TestAccountMove, self).setUp()

        self.company = self.env.ref('base.main_company')

        self.due_to_due_from_journal_main_company =\
            self.env['account.journal'].create(
                {'name': 'Test Due To/Due From', 'type': 'general',
                 'code': 'DUE',
                 'currency_id': self.company.currency_id.id,
                 'company_id': self.company.id})

        user_type_current_liabilities = self.env.ref(
            'account.data_account_type_current_liabilities')

        self.account_due_to_main_company = self.env['account.account'].create({
            'code': 'Test 101404',
            'name': 'Test Due To Account',
            'user_type_id': user_type_current_liabilities.id,
            'company_id': self.company.id
        })

        self.account_payroll_clearing_main_company =\
            self.env['account.account'].create({
                'code': 'Test 212410',
                'name': 'Test Payroll Clearing',
                'user_type_id': user_type_current_liabilities.id,
                'company_id': self.company.id
            })

        user_type_current_assets = self.env.ref(
            'account.data_account_type_current_assets')

        self.account_due_from_main_company =\
            self.env['account.account'].create({
                'code': 'Test 100020',
                'name': 'Test Due From Account',
                'user_type_id': user_type_current_assets.id,
                'company_id': self.company.id
            })

        user_type_current_expenses = self.env.ref(
            'account.data_account_type_expenses')

        self.account_salary_expense_main_company =\
            self.env['account.account'].create({
                'code': 'Test 212400',
                'name': 'Test Salary Expenses',
                'user_type_id': user_type_current_expenses.id,
                'company_id': self.company.id,
                'reconcile': True
            })

        self.company.due_fromto_payment_journal_id =\
            self.due_to_due_from_journal_main_company
        self.company.due_from_account_id = self.account_due_from_main_company
        self.company.due_to_account_id = self.account_due_to_main_company

        self.partner_company_one = self.env["res.partner"].sudo().create({
            "name": "Test Company One"
        })
        self.company_one = self.env["res.company"].sudo().create({
            "name": "Test Company One",
            "partner_id": self.partner_company_one.id,
            "parent_id": self.company.id
        })

        self.due_to_due_from_journal_company_one =\
            self.env['account.journal'].sudo().create(
                {'name': 'Test Due To/Due From', 'type': 'general',
                 'code': 'DUE',
                 'currency_id': self.company.currency_id.id,
                 'company_id': self.company_one.id})

        self.account_due_to_company_one =\
            self.env['account.account'].sudo().create({
                'code': 'Test 101404',
                'name': 'Test Due To Account',
                'user_type_id': user_type_current_liabilities.id,
                'company_id': self.company_one.id
            })

        self.account_due_from_company_one =\
            self.env['account.account'].sudo().create({
                'code': 'Test 100020',
                'name': 'Test Due From Account',
                'user_type_id': user_type_current_assets.id,
                'company_id': self.company_one.id
            })

        self.company_one.due_fromto_payment_journal_id =\
            self.due_to_due_from_journal_company_one
        self.company_one.due_from_account_id =\
            self.account_due_from_company_one
        self.company_one.due_to_account_id = self.account_due_to_company_one

        self.account_salary_expense_company_one =\
            self.env['account.account'].sudo().create({
                'code': 'Test 212400',
                'name': 'Test Salary Expenses',
                'user_type_id': user_type_current_expenses.id,
                'company_id': self.company_one.id,
                'reconcile': True
            })

        self.partner_company_two = self.env["res.partner"].sudo().create({
            "name": "Test Company Two"
        })
        self.company_two = self.env["res.company"].sudo().create({
            "name": "Test Company Two",
            "partner_id": self.partner_company_two.id,
            "parent_id": self.company.id
        })

        self.due_to_due_from_journal_company_two =\
            self.env['account.journal'].sudo().create(
                {'name': 'Test Due To/Due From', 'type': 'general',
                 'code': 'DUE',
                 'currency_id': self.company.currency_id.id,
                 'company_id': self.company_two.id})

        self.account_due_to_company_two =\
            self.env['account.account'].sudo().create({
                'code': 'Test 101404',
                'name': 'Test Due To Account',
                'user_type_id': user_type_current_liabilities.id,
                'company_id': self.company_two.id
            })

        self.account_due_from_company_two =\
            self.env['account.account'].sudo().create({
                'code': 'Test 100020',
                'name': 'Test Due From Account',
                'user_type_id': user_type_current_assets.id,
                'company_id': self.company_two.id
            })

        self.account_salary_expense_company_two =\
            self.env['account.account'].sudo().create({
                'code': 'Test 212400',
                'name': 'Test Salary Expenses',
                'user_type_id': user_type_current_expenses.id,
                'company_id': self.company_two.id,
                'reconcile': True
            })

        self.company_two.due_fromto_payment_journal_id =\
            self.due_to_due_from_journal_company_two
        self.company_two.due_from_account_id =\
            self.account_due_from_company_two
        self.company_two.due_to_account_id = self.account_due_to_company_two

        self.employee_A = self.env["res.partner"].create({
            'name': 'Employee A'
        })

        self.employee_B = self.env["res.partner"].create({
            'name': 'Employee B'
        })

        self.employee_C = self.env["res.partner"].create({
            'name': 'Employee C'
        })

        employee_group = self.env.ref('base.group_user')
        employee_invoice_group = self.env.ref('account.group_account_invoice')

        self.account_user = self.env["res.users"].\
            with_context({'no_reset_password': True}).create(dict(
                name="Adviser",
                company_id=self.company.id,
                login="fm",
                email="accountmanager@yourcompany.com",
                groups_id=[
                    (6, 0, [employee_group.id, employee_invoice_group.id])]
            ))

    def test_post(self):

        self.journalrec = self.env['account.journal'].sudo(
            self.account_user.id).search([('type', '=', 'general')])[0]

        payroll_move = self.env["account.move"].\
            sudo(self.account_user.id).create({
                'journal_id': self.journalrec.id,
                'company_id': self.company.id,
                'line_ids': [(0, 0, {
                    'account_id': self.account_salary_expense_main_company.id,
                    'partner_id': self.employee_B.id,
                    'debit': 1000
                }), (0, 0, {
                    'account_id': self.account_salary_expense_main_company.id,
                    'partner_id': self.employee_A.id,
                    'debit': 500
                }), (0, 0, {
                    'account_id': self.account_salary_expense_main_company.id,
                    'partner_id': self.employee_C.id,
                    'debit': 500,
                    'transfer_to_company_id': self.company_two.id
                }), (0, 0, {
                    'account_id': self.account_salary_expense_main_company.id,
                    'partner_id': self.employee_B.id,
                    'debit': 600,
                    'transfer_to_company_id': self.company_one.id
                }), (0, 0, {
                    'account_id': self.account_salary_expense_main_company.id,
                    'partner_id': self.employee_A.id,
                    'debit': 400,
                    'transfer_to_company_id': self.company_one.id
                }), (0, 0, {
                    'account_id':
                    self.account_payroll_clearing_main_company.id,
                    'credit': 3000,
                })
                ]
            })

        # Main company Due To/Due From Move Before Payroll Journal Entry Post
        main_company_due_tofrom_moves_before =\
            self.env['account.move'].sudo(self.account_user.id).search_count(
                [('journal_id', '=',
                    self.due_to_due_from_journal_main_company.id)])

        # Test Company One Due To/Due From Move Before Payroll Journal Entry
        # Post
        company_one_due_tofrom_moves_before =\
            self.env['account.move'].sudo(self.account_user.id).search_count(
                [('journal_id', '=',
                    self.due_to_due_from_journal_company_one.id),
                 ('company_id', '=', self.company_one.id)])

        # Test Company Two Due To/Due From Move Before Payroll Journal Entry
        # Post
        company_two_due_tofrom_moves_before =\
            self.env['account.move'].sudo(self.account_user.id).search_count(
                [('journal_id', '=',
                    self.due_to_due_from_journal_company_two.id),
                 ('company_id', '=', self.company_two.id)])

        payroll_move.post()

        # Main company Due To/Due From Move After Payroll Journal Entry Post
        main_company_due_tofrom_moves_after =\
            self.env['account.move'].sudo(self.account_user.id).search_count(
                [('journal_id', '=',
                    self.due_to_due_from_journal_main_company.id)])

        # Test Company One Due To/Due From Move After Payroll Journal Entry
        # Post
        company_one_due_tofrom_moves_after =\
            self.env['account.move'].sudo(self.account_user.id).search_count(
                [('journal_id', '=',
                    self.due_to_due_from_journal_company_one.id),
                 ('company_id', '=', self.company_one.id)])

        # Test Company Two Due To/Due From Move After Payroll Journal Entry
        # Post

        company_two_due_tofrom_moves_after =\
            self.env['account.move'].sudo(self.account_user.id).search_count(
                [('journal_id', '=',
                    self.due_to_due_from_journal_company_two.id),
                 ('company_id', '=', self.company_two.id)])

        # Check for Company One
        self.assertEqual(main_company_due_tofrom_moves_after,
                         main_company_due_tofrom_moves_before + 1)

        # Check moves for dedicated companies
        self.assertEqual(company_one_due_tofrom_moves_after,
                         company_one_due_tofrom_moves_before + 1)

        self.assertEqual(company_two_due_tofrom_moves_after,
                         company_two_due_tofrom_moves_before + 1)
