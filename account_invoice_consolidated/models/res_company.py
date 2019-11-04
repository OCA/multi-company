# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    cons_invoice_text = fields.Html()
    due_from_account_id = fields.Many2one('account.account', 'Due From')
    due_to_account_id = fields.Many2one('account.account', 'Due To')
    due_fromto_payment_journal_id = fields.Many2one(
        'account.journal', string="Due From/Due To Journal")
