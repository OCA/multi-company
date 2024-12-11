# Copyright 2018 Tecnativa - Carlos Dauden
# Copyright 2022 Moduon - Eduardo de Miguel
# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
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
        default=lambda s: s.env.company.currency_id,
    )
    chart_template = fields.Selection(
        selection="_chart_template_selection",
        required=True,
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
    default_sale_tax = fields.Selection(
        selection="_tax_selection",
        string="Default Sales Tax",
    )
    default_sale_tax_options = fields.Char(compute="_compute_default_sale_tax_options")
    force_sale_tax = fields.Boolean(
        string="Force Sale Tax In All Products",
        help="Set default sales tax to all products.\n"
        "If smart search product tax is also enabled matches founded "
        "will overwrite default taxes, but not founded will remain",
    )
    default_purchase_tax = fields.Selection(
        selection="_tax_selection",
    )
    default_purchase_tax_options = fields.Char(
        compute="_compute_default_purchase_tax_options"
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

    def _chart_template_selection(self):
        """We obtain those actually installed."""
        chart_template_options = []
        chart_template = self.env["account.chart.template"]
        for key, name in chart_template.with_context(
            chart_template_only_installed=True
        )._select_chart_template(self.env.company.country_id):
            chart_template_mapping = chart_template._get_chart_template_mapping()[key]
            if chart_template_mapping["installed"]:
                chart_template_options.append((key, name))
        return chart_template_options

    def _tax_selection(self):
        """We need to define in the selection all possible options."""
        tax_data_options = []
        for key, _name in self._chart_template_selection():
            tax_data = self.env["account.chart.template"]._get_chart_template_data(key)[
                "account.tax"
            ]
            for tax_key in list(tax_data.keys()):
                tax_key_custom = f"{key}-{tax_key}"
                tax_name_key = self.env.user.lang.split("_")[0]
                tax_data_item = tax_data[tax_key]
                description_key = f"description@{tax_name_key}"
                if "description" in tax_data_item and description_key in tax_data_item:
                    tax_name = tax_data_item[description_key]
                else:
                    tax_name = tax_data_item["name"]
                tax_data_options.append((tax_key_custom, tax_name))
        return tax_data_options

    def _get_tax_options(self, type_tax_use="sale"):
        tax_options = []
        if self.chart_template:
            chart_template = self.chart_template
            tax_data = self.env["account.chart.template"]._get_chart_template_data(
                chart_template
            )["account.tax"]
            for key in list(tax_data.keys()):
                if tax_data[key]["type_tax_use"] == type_tax_use:
                    tax_options.append(f"{chart_template}-{key}")
        return tax_options

    @api.depends("chart_template")
    def _compute_default_sale_tax_options(self):
        for item in self:
            allowed_options = item._get_tax_options(type_tax_use="sale")
            item.default_sale_tax_options = ",".join(allowed_options)

    @api.depends("chart_template")
    def _compute_default_purchase_tax_options(self):
        for item in self:
            allowed_options = item._get_tax_options(type_tax_use="purchase")
            item.default_purchase_tax_options = ",".join(allowed_options)

    def create_bank_journals(self):
        AccountJournal = self.env["account.journal"].sudo()
        AccountAccount = self.env["account.account"].sudo()
        ResPartnerBank = self.env["res.partner.bank"].sudo()
        bank_journals = AccountJournal.search(
            [("type", "=", "bank"), ("company_id", "=", self.new_company_id.id)]
        )
        vals = {
            "type": "bank",
            "company_id": self.new_company_id.id,
        }
        for i, bank_wiz in enumerate(self.bank_ids):
            bank = ResPartnerBank.create(
                {
                    "acc_number": bank_wiz.acc_number,
                    "bank_id": bank_wiz.bank_id.id,
                    "partner_id": self.new_company_id.partner_id.id,
                    "company_id": self.new_company_id.id,
                    "allow_out_payment": bank_wiz.allow_out_payment,
                }
            )
            vals.update(
                {
                    "name": bank.acc_number,
                    "bank_acc_number": bank.acc_number,
                }
            )
            if i < len(bank_journals):
                bank_journals[i].update(vals)
            else:
                account_account = AccountAccount.create(
                    {
                        "code": f"57200{i + 1}",
                        "name": vals["name"],
                        "account_type": "asset_cash",
                        "company_id": vals["company_id"],
                    }
                )
                vals.update(
                    {
                        "code": f"BNK{i + 1}",
                        "sequence": bank_journals[0].sequence or i,
                        "default_account_id": account_account.id,
                    }
                )
                AccountJournal.create(vals)

    def create_sequences(self):
        for sequence in self.sudo().sequence_ids:
            sequence.copy({"company_id": self.new_company_id.id})

    def create_company(self):
        self.new_company_id = self.env["res.company"].create(
            {
                "name": self.name,
                "user_ids": [(6, 0, self.user_ids.ids)],
                "currency_id": self.currency_id.id,
            }
        )
        allowed_company_ids = (
            self.env.context.get("allowed_company_ids", []) + self.new_company_id.ids
        )
        new_company = self.new_company_id.with_context(
            allowed_company_ids=allowed_company_ids
        )
        self.env["account.chart.template"].try_loading(self.chart_template, new_company)
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
            record = self.env.ref(f"{module}.{company_id}_{name}", False)
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

    def set_product_taxes(self, default_sale_tax, default_purchase_tax):
        user_company = self.env.user.company_id
        new_company = self.new_company_id
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
            sale_tax = default_sale_tax or new_company.account_sale_tax_id
            (products - updated_sale).update({"taxes_id": [(4, sale_tax.id)]})
        if self.smart_search_product_tax:
            for product in products.filtered("supplier_taxes_id"):
                if self.update_product_taxes(
                    product, "supplier_taxes_id", user_company
                ):
                    updated_purchase |= product
        if self.update_default_taxes and self.force_purchase_tax:
            purchase_tax = default_purchase_tax or new_company.account_purchase_tax_id
            (products - updated_purchase).update(
                {
                    "supplier_taxes_id": [(4, purchase_tax.id)],
                }
            )

    def update_taxes(self):
        if self.update_default_taxes:
            IrDefault = self.env["ir.default"].sudo()
            new_company = self.new_company_id
            sale_tax = False
            if self.default_sale_tax:
                tax_key = self.default_sale_tax.replace(f"{self.chart_template}-", "")
                full_xmlid = (
                    f"account.{new_company.id}_{tax_key}"
                    if "." not in tax_key
                    else tax_key
                )
                sale_tax = self.env.ref(full_xmlid, raise_if_not_found=False)
                IrDefault.set(
                    model_name="product.template",
                    field_name="taxes_id",
                    value=sale_tax.ids,
                    company_id=new_company.id,
                )
                new_company.account_sale_tax_id = sale_tax
            purchase_tax = False
            if self.default_purchase_tax:
                tax_key = self.default_purchase_tax.replace(
                    f"{self.chart_template}-", ""
                )
                full_xmlid = (
                    f"account.{new_company.id}_{tax_key}"
                    if "." not in tax_key
                    else tax_key
                )
                purchase_tax = self.env.ref(full_xmlid, raise_if_not_found=False)
                IrDefault.set(
                    model_name="product.template",
                    field_name="supplier_taxes_id",
                    value=purchase_tax.ids,
                    company_id=new_company.id,
                )
                new_company.account_purchase_tax_id = purchase_tax
        self.set_product_taxes(sale_tax, purchase_tax)

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
                ("value_reference", "=like", f"{model},%"),
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
                        "value_reference": f"{model},{new_ref.id}",
                        "value_float": False,
                        "value_integer": False,
                    }
                )

    def update_properties(self):
        if self.smart_search_specific_account:
            self.set_specific_properties("account.account", "code")
        if self.smart_search_fiscal_position:
            self.set_specific_properties("account.fiscal.position", "name")

    def action_res_company_form(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "base.action_res_company_form"
        )
        form = self.env.ref("base.view_company_form")
        action["views"] = [(form.id, "form")]
        action["res_id"] = self.new_company_id.id
        return action

    def action_accept(self):
        self.create_company()
        self.update_taxes()
        self.update_properties()
        return self.action_res_company_form()

    @api.onchange("chart_template")
    def onchange_chart_template(self):
        if self.chart_template:
            chart_template_mapping = self.env[
                "account.chart.template"
            ]._get_chart_template_mapping()[self.chart_template]
            country_id = chart_template_mapping.get("country_id")
            if country_id:
                country = self.env["res.country"].browse(country_id)
                self.currency_id = country.currency_id


class AccountMulticompanyBankWiz(models.TransientModel):
    """Wizard used to create res.partner.bank records"""

    _name = "account.multicompany.bank.wiz"
    _order = "id"
    _description = "Wizard Account Multi-company Bank"

    wizard_id = fields.Many2one(
        comodel_name="account.multicompany.easy.creation.wiz",
    )
    acc_number = fields.Char(
        string="Account Number",
        required=True,
    )
    bank_id = fields.Many2one(
        comodel_name="res.bank",
        string="Bank",
    )
    allow_out_payment = fields.Boolean(
        string="Allow Out Payments",
        default=True,
    )
