# Copyright 2018 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import ormcache
from odoo.tools.safe_eval import safe_eval


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _name = "account.multicompany.easy.creation.wiz"
    _description = "Wizard Account Multi-company Easy Creation"

    def _default_sequence_ids(self):
        # this is a "trick" for avoiding glue modules
        exclude_seq_list = self.env["ir.config_parameter"].get_param(
            "account_multicompany_easy_creation.exclude_sequence_list",
            [
                False,
                "aeat.sequence.type",
                "pos.config.simplified_invoice",
                "stock.scrap",
            ],
        )
        if not isinstance(exclude_seq_list, list):
            exclude_seq_list = safe_eval(exclude_seq_list)
        return self.env["ir.sequence"].search(
            [
                ("company_id", "=", self.env.user.company_id.id),
                ("code", "not in", exclude_seq_list),
            ]
        )

    name = fields.Char(
        string="Company Name",
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        required=True,
        default=lambda s: s.env.user.company_id.currency_id,
    )
    chart_template_id = fields.Many2one(
        comodel_name="account.chart.template",
        string="Chart Template",
    )
    bank_ids = fields.One2many(
        comodel_name="account.multicompany.bank.wiz",
        inverse_name="wizard_id",
        string="Bank accounts to create",
    )
    user_ids = fields.Many2many(
        comodel_name="res.users",
        string="Users allowed",
        domain=[("share", "=", False)],
    )
    sequence_ids = fields.Many2many(
        comodel_name="ir.sequence",
        string="Sequences to create",
        default=lambda s: s._default_sequence_ids(),
    )
    new_company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
    )
    # TAXES
    smart_search_product_tax = fields.Boolean(
        default=True,
        help="Go over product taxes in actual company to match and set "
        "equivalent taxes in then new company.",
    )
    update_default_taxes = fields.Boolean(
        help="Update default taxes applied to local transactions",
    )
    default_sale_tax_id = fields.Many2one(
        comodel_name="account.tax.template",
        string="Default Sales Tax",
    )
    force_sale_tax = fields.Boolean(
        string="Force Sale Tax In All Products",
        help="Set default sales tax to all products.\n"
        "If smart search product tax is also enabled matches founded "
        "will overwrite default taxes, but not founded will remain",
    )
    default_purchase_tax_id = fields.Many2one(
        comodel_name="account.tax.template",
        string="Default Purchase Tax",
    )
    force_purchase_tax = fields.Boolean(
        string="Force Purchase Tax In All Products",
        help="Set default purchase tax to all products.\n"
        "If smart search product tax is also enabled matches founded "
        "will overwrite default taxes, but not founded will remain",
    )
    # ACCOUNTS
    smart_search_specific_account = fields.Boolean(
        default=True,
        help="Go over specific accounts in actual company to match and set "
        "equivalent taxes in the new company.\n"
        "Applies to products, categories, partners, ...",
    )
    smart_search_fiscal_position = fields.Boolean(
        default=True,
        help="Go over partner fiscal positions in actual company to match "
        "and set equivalent fiscal positions in the new company.",
    )
    update_default_accounts = fields.Boolean(
        help="Update default accounts defined in account chart template",
    )
    account_receivable_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Default Receivable Account",
    )
    account_payable_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Default Payable Account",
    )
    account_income_categ_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Default Category Income Account",
    )
    account_expense_categ_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Default Category Expense Account",
    )

    def create_bank_journals(self):
        AccountJournal = self.env["account.journal"].sudo()
        AccountAccount = self.env["account.account"].sudo()
        bank_journals = AccountJournal.search(
            [("type", "=", "bank"), ("company_id", "=", self.new_company_id.id)]
        )
        vals = {
            "type": "bank",
            "company_id": self.new_company_id.id,
        }
        for i, bank in enumerate(self.bank_ids):
            vals.update({"name": bank.acc_number, "bank_acc_number": bank.acc_number})
            if i < len(bank_journals):
                bank_journals[i].update(vals)
            else:
                account_account = AccountAccount.create(
                    {
                        "code": "57200X",
                        "name": vals["name"],
                        "user_type_id": self.env.ref(
                            "account.data_account_type_liquidity"
                        ).id,
                        "company_id": vals["company_id"],
                    }
                )
                vals.update(
                    {
                        "code": False,
                        "sequence_id": False,
                        "default_debit_account_id": account_account.id,
                        "default_credit_account_id": account_account.id,
                    }
                )
                AccountJournal.create(vals)

    def create_sequences(self):
        for sequence in self.sudo().sequence_ids:
            sequence.copy({"company_id": self.new_company_id.id})

    def create_company(self):
        self.new_company_id = self.env["res.company"].create(
            {"name": self.name, "user_ids": [(6, 0, self.user_ids.ids)]}
        )
        allowed_company_ids = (
            self.env.context.get("allowed_company_ids", []) + self.new_company_id.ids
        )
        new_company = self.new_company_id.with_context(
            allowed_company_ids=allowed_company_ids
        )
        self.with_context(
            allowed_company_ids=allowed_company_ids
        ).chart_template_id.try_loading(company=new_company)
        self.create_bank_journals()
        self.create_sequences()

    @ormcache("self.id", "company_id", "match_taxes")
    def taxes_by_company(self, company_id, match_taxes):
        xml_ids = match_taxes.sudo().get_external_id().values()
        # If any tax doesn't have xml, we won't be able to match it
        record_ids = []
        for xml_id in xml_ids:
            if not xml_id:
                continue
            module, ref = xml_id.split(".", 1)
            _company, name = ref.split("_", 1)
            record = self.env.ref("{}.{}_{}".format(module, company_id, name), False)
            if record:
                record_ids.append(record.id)
        return record_ids

    def update_product_taxes(self, product, taxes_field, company_from):
        product_taxes = product[taxes_field].filtered(
            lambda tax: tax.company_id == company_from
        )
        tax_ids = product_taxes and self.taxes_by_company(
            self.new_company_id.id, product_taxes
        )
        if tax_ids:
            product.update({taxes_field: [(4, tax_id) for tax_id in tax_ids]})
            return True
        return False

    def match_tax(self, tax_template):
        """We can only match the new company tax if the chart was used"""
        xml_id = tax_template and tax_template.get_external_id().get(tax_template.id)
        if not xml_id:
            raise ValidationError(
                _("This tax template can't be match without xml_id: '%s'")
                % tax_template.name
            )
        module, name = xml_id.split(".", 1)
        return self.sudo().env.ref(
            "{}.{}_{}".format(module, self.new_company_id.id, name)
        )

    def set_product_taxes(self):
        user_company = self.env.user.company_id
        products = (
            self.env["product.product"]
            .sudo()
            .search(
                [
                    "&",
                    ("company_id", "=", False),
                    "|",
                    ("taxes_id", "!=", False),
                    ("supplier_taxes_id", "!=", False),
                ]
            )
        )
        updated_sale = updated_purchase = products.browse()
        if self.smart_search_product_tax:
            for product in products.filtered("taxes_id"):
                if self.update_product_taxes(product, "taxes_id", user_company):
                    updated_sale |= product
        if self.update_default_taxes and self.force_sale_tax:
            (products - updated_sale).update(
                {"taxes_id": [(4, self.match_tax(self.default_sale_tax_id).id)]}
            )
        if self.smart_search_product_tax:
            for product in products.filtered("supplier_taxes_id"):
                if self.update_product_taxes(
                    product, "supplier_taxes_id", user_company
                ):
                    updated_purchase |= product
        if self.update_default_taxes and self.force_purchase_tax:
            (products - updated_purchase).update(
                {
                    "supplier_taxes_id": [
                        (4, self.match_tax(self.default_purchase_tax_id).id)
                    ],
                }
            )

    def update_taxes(self):
        if self.update_default_taxes:
            IrDefault = self.env["ir.default"].sudo()
            if self.default_sale_tax_id:
                IrDefault.set(
                    model_name="product.template",
                    field_name="taxes_id",
                    value=self.match_tax(self.default_sale_tax_id).ids,
                    company_id=self.new_company_id.id,
                )
            if self.default_purchase_tax_id:
                IrDefault.set(
                    model_name="product.template",
                    field_name="supplier_taxes_id",
                    value=self.match_tax(self.default_purchase_tax_id).ids,
                    company_id=self.new_company_id.id,
                )
        self.set_product_taxes()

    def set_specific_properties(self, model, match_field):
        user_company = self.env.user.company_id
        self_sudo = self.sudo()
        new_company_id = self.new_company_id.id
        IrProperty = self_sudo.env["ir.property"]
        properties = IrProperty.search(
            [
                ("company_id", "=", user_company.id),
                ("type", "=", "many2one"),
                ("res_id", "!=", False),
                ("value_reference", "=like", "{},%".format(model)),
            ]
        )
        Model = self_sudo.env[model]
        for prop in properties:
            ref = Model.browse(int(prop.value_reference.split(",")[1]))
            new_ref = Model.search(
                [
                    ("company_id", "=", new_company_id),
                    (match_field, "=", ref[match_field]),
                ]
            )
            if new_ref:
                prop.copy(
                    {
                        "company_id": new_company_id,
                        "value_reference": "{},{}".format(model, new_ref.id),
                        "value_float": False,
                        "value_integer": False,
                    }
                )

    def match_account(self, account_template):
        return (
            self.sudo()
            .env["account.account"]
            .search(
                [
                    ("company_id", "=", self.new_company_id.id),
                    ("code", "=", account_template.code),
                ],
                limit=1,
            )
        )

    def set_global_properties(self):
        IrProperty = self.env["ir.property"].sudo()
        todo_list = [
            (
                "property_account_receivable_id",
                "res.partner",
                "account.account",
                self.match_account(self.account_receivable_id).id,
            ),
            (
                "property_account_payable_id",
                "res.partner",
                "account.account",
                self.match_account(self.account_payable_id).id,
            ),
            (
                "property_account_expense_categ_id",
                "product.category",
                "account.account",
                self.match_account(self.account_expense_categ_id).id,
            ),
            (
                "property_account_income_categ_id",
                "product.category",
                "account.account",
                self.match_account(self.account_income_categ_id).id,
            ),
        ]
        new_company = self.new_company_id
        for record in todo_list:
            if not record[3]:
                continue
            field = self.env["ir.model.fields"].search(
                [
                    ("name", "=", record[0]),
                    ("model", "=", record[1]),
                    ("relation", "=", record[2]),
                ],
                limit=1,
            )
            vals = {
                "name": record[0],
                "company_id": new_company.id,
                "fields_id": field.id,
                "value": "{},{}".format(record[2], record[3]),
            }
            properties = IrProperty.search(
                [("name", "=", record[0]), ("company_id", "=", new_company.id)]
            )
            if properties:
                properties.write(vals)
            else:
                IrProperty.create(vals)

    def update_properties(self):
        if self.smart_search_specific_account:
            self.set_specific_properties("account.account", "code")
        if self.smart_search_fiscal_position:
            self.set_specific_properties("account.fiscal.position", "name")
        if self.update_default_accounts:
            self.set_global_properties()

    def action_res_company_form(self):
        action = self.env.ref("base.action_res_company_form").read()[0]
        form = self.env.ref("base.view_company_form")
        action["views"] = [(form.id, "form")]
        action["res_id"] = self.new_company_id.id
        return action

    def action_accept(self):
        self.create_company()
        self.update_taxes()
        self.update_properties()
        return self.action_res_company_form()


class AccountMulticompanyBankWiz(models.TransientModel):
    _inherit = "res.partner.bank"
    _name = "account.multicompany.bank.wiz"
    _order = "id"
    _description = "Wizard Account Multi-company Bank"

    wizard_id = fields.Many2one(
        comodel_name="account.multicompany.easy.creation.wiz",
    )
    partner_id = fields.Many2one(
        required=False,
    )
