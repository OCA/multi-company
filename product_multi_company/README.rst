.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==========================================
Product permissions for discrete companies
==========================================

This modules allows to select in which of the companies you want to use each
of the product templates.

Installation
============

This module uses the post and uninstall hooks for updating default product
template security rule. This only means that updating the module will not
restore the security rule this module changes. Only a complete removal and
reinstallation will serve.

Usage
=====

On the product form view, go to the "Information" tab, and put the companies
in which you want to use that product. If none is selected, the product will
be visible in all of them. The default value is the current one.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/133/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/multi-company/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

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
