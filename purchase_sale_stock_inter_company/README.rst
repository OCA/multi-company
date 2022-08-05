.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================================
Purchase Sale Stock Inter Company
=================================

This module is useful if there are multiple companies in the same Odoo database and those companies sell goods or services among themselves.
It allows to create a sale order in company A from a purchase order in company B.

Imagine you have company A and company B in the same Odoo database:

* Company A purchase goods from company B.
* Company A will create a purchase order with company B as supplier.
* This module automate the creation of the sale order in company B with company A as customer.

**Table of contents**

.. contents::
   :local:

Configuration
=============

To configure this module, you need to:
#. go to the menu *General Settings > Companies > Companies*.
#. Select one of the companies.
#. Go to the tab *Inter-Company* then the group *Purchase To Sale*.
#. If you check the option *Sale Auto Validation* in the configuration of company B, then when you validate a *Purchase Order* in company A with company B as supplier, the *Sale Order* will be automatically validated in company B with company A as customer.

Known issues / Roadmap
======================

* If you want also to have different warehouses for your sales orders you can install `stock` and `purchase_sale_stock_inter_company` will be auto installed.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/multi-company/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/OCA/multi-company/issues/new?body=module:%20purchase_sale_inter_company%0Aversion:%2015.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Odoo SA
* Akretion
* Tecnativa

Contributors
~~~~~~~~~~~~

* Odoo S.A. (original module `inter_company_rules`)
* Andrea Stirpe <a.stirpe@onestein.nl>
* Adria Gil Sorribes <adria.gil@forgeflow.com>
* Christopher Ormaza <chris.ormaza@forgeflow.com>
* `Akretion <https://www.akretion.com>`:

  * Chafique Delli <chafique.delli@akretion.com>
  * Alexis de Lattre <alexis.delattre@akretion.com>
  * David Beal <david.beal@akretion.com>
* `Tecnativa <https://www.tecnativa.com>`:

  * Jairo Llopis
  * David Vidal
  * Pedro M. Baeza
* `Camptocamp <https://www.camptocamp.com>`:

  * Maksym Yankin <maksym.yankin@camptocamp.com>

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/multi-company <https://github.com/OCA/multi-company/tree/15.0/purchase_sale_inter_company>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
