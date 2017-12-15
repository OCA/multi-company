.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==========================================
Partner permissions for discrete companies
==========================================

This modules allows to select in which of the companies you want to use each
of the partners.

Installation
============

This module uses the post and uninstall hooks for updating default partner
template security rule. This only means that updating the module will not
restore the security rule this module changes. Only a complete removal and
reinstallation will serve.

It uses a module from https://github.com/OCA/server-tools called
*base_suspend_security* that you must have available in your Odoo installation.

Usage
=====

On the partner form view, go to the "Sales & Purchases" tab, and put the
companies in which you want to use that partner. If none is selected, the
partner will be visible in all of them. The default value is the current one.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/133/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/multi-company/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Known issues/Roadmap
====================

* Allow to select different companies from the parent in contacts.

Credits
=======

Contributors
------------

* Oihane Crucelaegui <oihanecruce@gmail.com>
* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* Dave Lasley <dave@laslabs.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
