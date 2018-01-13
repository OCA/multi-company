.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=============================
Account Invoice Inter Company
=============================

This module is usefull if there are multiple companies in the same Odoo database and those companies sell goods or services among themselves.
It allow to create an invoice in company A from an invoice in company B.

Imagine you have company A and company B in the same Odoo database.
First scenario: company B create an invoice with company A as customer. The module will automate the generation of the supplier invoice in company A.
Second scenario: company A create an invoice with company B as supplier. The module will automate the generation of the customer invoice in company B.


Configuration
=============

To configure this module, you need to go to the menu *Settings > Users & Companies > Companies*, select one of the companies and go to the tab *Inter-Company* then the group *Invoice*.


Usage
=====

If you choose the option *Invoice Auto Validation* in the configuration of company B, when you validate a *Customer Invoice* in company A with company B as customer, then the *Supplier Invoice* will be automatically validated in company B with company A as supplier.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/133/11.0


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/multi-company/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smash it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Odoo S.A. (original module `inter_company_rules`)
* Chafique Delli <chafique.delli@akretion.com>
* Alexis de Lattre <alexis.delattre@akretion.com>
* Andrea Stirpe <a.stirpe@onestein.nl>

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
