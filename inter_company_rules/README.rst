.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===================
Inter Company Rules
===================

This module is usefull if there are multiple companies in the same Odoo database and those companies sell goods or services among themselves.

Imagine you have company A and company B in the same Odoo database and company A purchase goods from company B: company A will create a purchase.order with company B as supplier, and company B will have to create a sale order with company A as supplier. This module automate the creation of the sale order in company B.

You can also opt for another scenario: company B create an invoice with company A as customer. The module will automate the generation of the supplier invoice in company A.

Configuration
=============

To configure this module, you need to go to the menu *Settings > Companies > Companies*, select one of the companies and go to the tab *Inter-Company Rules*. You have to choose which scenario you want to have for interactions between companies: either automate the creation of sale.order / purchase.order between companies, or automate the creation of customer invoice / supplier invoice between companies (you cannot do both).

Another important configuration is the *Inter Company User* : it is the user that will be used to automatically generate the corresponding object in the other company. One important thing to understand is that the fields *Customer Taxes* (technical field field: *taxes_id*) and *Supplier Taxes* (technical field field: *supplier_taxes_id*) on product.template are **NOT** property fields (in new API, we would say: *company_dependant=False*). Therefore, it is only the multi-company record rule on account.tax that make sure that, for a particular product, the taxes for company A are selected when you invoice this product in company A and the taxes for company B are selected when you invoice this product in company B. So you cannot select the administrator as *Inter Company User* because this user by-passes the record rules ; you have to select a regular user that is attached to the company and only to this company (don't select a user that is allowed to switch between companies). Special per-company filtering of taxes has been added in the *product_id_change* method in of sale.order.line and purchase.order.line (cf `this commit <https://github.com/odoo/odoo/commit/eb993b7f3bb93a951a63c5db73ca069ba8f835c3>`_ for the purchase.order.line, dated December 11th 2015), but this filtering is not yet present in the *product_id_change* method of account.invoice.line. When this per-company filtering of taxes will be present on account.invoice.line, we will be able to use *admin* as the *Inter Company User*.

Usage
=====

If you choose the option *Create Invoices/Refunds when encoding invoices/refunds made to this company* in the configuration of company B, when you validate a *Customer Invoice* in company A with company B as customer, then a *Supplier Invoice* will be automatically created in company B with company A as supplier.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/133/8.0


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/multi-company/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed `feedback
<https://github.com/OCA/
multi-company/issues/new?body=module:%20
inter_company_rules%0Aversion:%20
8.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------

* Odoo S.A.
* Chafique Delli <chafique.delli@akretion.com>
* Alexis de Lattre <alexis.delattre@akretion.com>
* Lorenzo Battistini <lorenzo.battistini@agilebg.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
