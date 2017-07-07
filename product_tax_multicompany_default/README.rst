.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================================
Product Tax Multi Company Default
=================================

This module sets the default company taxes for all the existing companies when
a product is created. It also adds a button to set all the taxes from other
companies matching them by tax code.

Configuration
=============

#. As obvious, you need to have several companies.
#. Go to Accounting > Configuration > Settings
#. Select the proper company (if you are admin or a user with several companies
   access), or keep the current one (for a regular user).
#. On Invoicing & Payments section, set fields "Default Sale Tax" and "Default
   Purchase Tax".

Usage
=====

To use this module, you need to:

#. Go to Sales > Sales > Products.
#. Create a new product and save it.
#. Switching user company (or being as admin or user with several companies
   access), you will see that the product has the default taxes for all the
   companies.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/133/9.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/multi-company/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
* Pedro M. Baeza <pedro.baeza@tecnativa.com>

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
