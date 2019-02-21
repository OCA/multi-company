.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===========================
Purchase Sale Inter Company
===========================

This module is useful if there are multiple companies in the same Odoo database and those companies sell goods or services among themselves.
It allows to create a sale order in company A from a purchase order in company B.

Imagine you have company A and company B in the same Odoo database:

* Company A purchase goods from company B.
* Company A will create a purchase order with company B as supplier.
* This module automate the creation of the sale order in company B with company A as customer.


Configuration
=============

To configure this module, you need to:
#. go to the menu *Settings > Companies > Companies*.
#. Select one of the companies.
#. Go to the tab *Inter-Company* then the group *Purchase To Sale*.
#. Select the *Warehouse For Sale Orders*, it is the warehouse that will be used to automatically generate the sale order in the other company.
#. If you check the option *Sale Auto Validation* in the configuration of company B, then when you validate a *Purchase Order* in company A with company B as supplier, the *Sale Order* will be automatically validated in company B with company A as customer.

Usage
=====

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/133/12.0


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/multi-company/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smash it by providing detailed and welcomed
feedback.

Credits
=======

Contributors
------------

* Odoo S.A.
* Chafique Delli <chafique.delli@akretion.com>
* Alexis de Lattre <alexis.delattre@akretion.com>
* Lorenzo Battistini <lorenzo.battistini@agilebg.com>
* `Tecnativa <https://www.tecnativa.com>`_:

  * Carlos Dauden
  * Jairo Llopis
* Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>

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
