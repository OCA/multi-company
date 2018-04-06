.. image:: https://img.shields.io/badge/license-LGPL--3-blue.png
   :target: https://www.gnu.org/licenses/lgpl
   :alt: License: LGPL-3

============================
Mcfix Base Model Create Hook
============================

This module intends to provide a temporary fixes for a issues that should
be fixed upstream. See https://github.com/odoo/odoo/pull/21219.

Known issues:

* When creating a company from scratch, it creates a partner with the
  default company.

* When writing the company in a partner, it doesn't write the company in the
  partner children.

* When creating a parent record for a record, it doesn't pass the company of
  the record.

Fixes introduced by this module:

* When creating a company from scratch, it creates a partner
  without any company.

* When writing the company in a partner, it writes the company in the
  partner and all its children at the same time.

* When creating a parent record for a record, it passes the company of
  the record if possible.


Installation
============

To install this module, simply follow the standard install process.


Usage
=====

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/133/11.0


Credits
=======

Contributors
------------

* Enric Tobella <etobella@creublanca.es>
* Jordi Ballester <jordi.ballester@eficent.com>
* Miquel Raïch <miquel.raich@eficent.com>

Do not contact contributors directly about support or help with technical issues.

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
