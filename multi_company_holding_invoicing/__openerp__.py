# -*- coding: utf-8 -*-
# © 2016 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{'name': 'Multi Company Holding Invoicing',
 'version': '1.0',
 'category': 'Accounting & Finance',
 'author': 'Akretion, Odoo Community Association (OCA)',
 'website': 'http://www.akretion.com/',
 'license': 'AGPL-3',
 'depends': [
     'sale',
     'sales_team',
     'inter_company_rules',
     'base_suspend_security',
     # Note we depend of this module for having the sale_ids field
     # on the invoice
     'sale_automatic_workflow',
 ],
 'data': [
     'config/sale_config.yml',
     'views/sales_team_view.xml',
     'views/sale_view.xml',
     'views/account_invoice_view.xml',
     'security/stock_security.xml',
     'wizards/wizard_holding_invoicing_view.xml',
     'wizards/sale_make_invoice_view.xml',
 ],
 'demo': [
     'demo/res_company_demo.xml',
     'demo/res_users_demo.xml',
     'demo/sales_team_demo.xml',
     'demo/sale_order_demo.xml',
     'demo/account_config.yml',
 ],
 'installable': True,
 }
