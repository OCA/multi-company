# -*- coding: utf-8 -*-
# © 2016 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp.tests.common import TransactionCase
from datetime import datetime

XML_COMPANY_A = 'multi_company_holding_invoicing.child_company_a'
XML_COMPANY_B = 'multi_company_holding_invoicing.child_company_b'
XML_COMPANY_HOLDING = 'base.main_company'
XML_SECTION_1 = 'multi_company_holding_invoicing.section_market_1'
XML_SECTION_2 = 'multi_company_holding_invoicing.section_market_2'
XML_PARTNER_ID = 'base.res_partner_2'


class CommonInvoicing(TransactionCase):

    def _get_sales(self, xml_ids):
        sales = self.env['sale.order'].browse(False)
        for xml_id in xml_ids:
            sale = self.env.ref(
                'multi_company_holding_invoicing.sale_order_%s' % xml_id)
            sales |= sale
        return sales

    def _validate_and_deliver_sale(self, xml_ids):
        sales = self._get_sales(xml_ids)
        for sale in sales:
            sale.action_button_confirm()
            for picking in sale.picking_ids:
                picking.force_assign()
                picking.do_transfer()
        return sales

    def _set_partner(self, sale_xml_ids, partner_xml_id):
        partner = self.env.ref(partner_xml_id)
        sales = self._get_sales(sale_xml_ids)
        sales.write({
            'partner_id': partner.id,
            'partner_invoice_id': partner.id,
            'partner_shipping_id': partner.id,
            })

    def _set_company(self, sale_xml_ids, company_xml_id):
        company = self.env.ref(company_xml_id)
        sales = self._get_sales(sale_xml_ids)
        sales.write({'company_id': company.id})

    def _set_section(self, sale_xml_ids, section_xml_id):
        section = self.env.ref(section_xml_id)
        sales = self._get_sales(sale_xml_ids)
        sales.write({'section_id': section.id})

    def _generate_holding_invoice(self, section_xml_id):
        date_invoice = datetime.today()
        wizard = self.env['wizard.holding.invoicing'].create({
            'section_id': self.ref(section_xml_id),
            'date_invoice': date_invoice,
            })
        res = wizard.create_invoice()
        invoices = self.env['account.invoice'].browse(res['domain'][0][2])
        return invoices

    def _check_number_of_invoice(self, invoices, number):
        self.assertEqual(
            len(invoices), 1,
            msg="Only one invoice should have been created, %s created"
                % len(invoices))

    def _check_invoiced_sale_order(self, invoice, sales):
        self.assertEqual(
            sales,
            invoice.holding_sale_ids,
            msg="Expected sale order to be invoiced %s found %s"
                % (', '.join(sales.mapped('name')),
                   ', '.join(invoice.holding_sale_ids.mapped('name'))))

    def _check_expected_invoice_amount(self, invoice, expected_amount):
        self.assertEqual(
            expected_amount, invoice.amount_total,
            msg="The amount invoiced should be %s, found %s"
                % (expected_amount, invoice.amount_total))

    def _check_child_invoice(self, invoice):
        company2sale = {}
        for sale in invoice.holding_sale_ids:
            if not company2sale.get(sale.company_id.id):
                company2sale[sale.company_id.id] = sale
            else:
                company2sale[sale.company_id.id] |= sale
        for child in invoice.child_invoice_ids:
            expected_sales = company2sale.get(child.company_id.id)
            if expected_sales:
                expected_sales_name = ', '.join(expected_sales.mapped('name'))
            else:
                expected_sales_name = ''
            if child.sale_ids:
                found_sales_name = ', '.join(child.sale_ids.mapped('name'))
            else:
                found_sales_name = ''
            self.assertEqual(
                child.sale_ids, expected_sales,
                msg="The child invoice generated is not linked to the "
                    "expected sale order. Found %s, expected %s"
                    % (found_sales_name, expected_sales_name))

    def _check_child_invoice_amount(self, invoice):
        discount = invoice.section_id.holding_discount
        expected_amount = invoice.amount_total * (1 - discount/100)
        computed_amount = 0
        for child in invoice.child_invoice_ids:
            computed_amount += child.amount_total
        self.assertAlmostEqual(
            expected_amount,
            computed_amount,
            msg="The total amoutn of child invoice is %s expected %s"
                % (computed_amount, expected_amount))

    def _check_sale_state(self, sales, expected_state):
        for sale in sales:
            self.assertEqual(
                sale.invoice_state, expected_state,
                msg="Invoice state is '%s' indeed of '%s'"
                    % (sale.invoice_state, expected_state))

    def _process_and_check_sale(
            self, section_xml_id, sale_xml_ids, expected_xml_ids):
        "This function will test a full scenario of invoicing."
        # tests are called before register_hook
        # register suspend_security hook
        self.env['ir.rule']._register_hook()

        # Check if current state of sale order is correct
        sales = self._get_sales(sale_xml_ids)
        self._check_sale_state(sales, 'not_ready')

        # Validate the sale order (sale_xml_ids) and check the state
        self._validate_and_deliver_sale(sale_xml_ids)
        sales = self._get_sales(expected_xml_ids)
        self._check_sale_state(sales, 'invoiceable')

        # Generate the holding invoice and check the :
        # - sales invoiced
        # - sales state
        # - invoiced amount
        invoice = self._generate_holding_invoice(section_xml_id)
        self._check_number_of_invoice(invoice, 1)
        sales_expected = self._get_sales(expected_xml_ids)
        self._check_invoiced_sale_order(invoice, sales_expected)
        self._check_sale_state(sales_expected, 'pending')
        expected_amount = sum(sales_expected.mapped('amount_total'))
        self._check_expected_invoice_amount(invoice, expected_amount)

        # Validad Invoice and check sale invoice state
        invoice.signal_workflow('invoice_open')
        self._check_sale_state(sales_expected, 'invoiced')

        # Generate the child invoice and check
        # - that child invoice have been generated
        # - check the invoiced amount
        # - check the sale state
        invoice.generate_child_invoice()
        self._check_child_invoice(invoice)
        self._check_child_invoice_amount(invoice)
        return invoice
