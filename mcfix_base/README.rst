.. image:: https://img.shields.io/badge/license-LGPL--3-blue.png
   :target: https://www.gnu.org/licenses/lgpl
   :alt: License: LGPL-3

==========
Mcfix Base
==========

This module is part of a set of modules that are intended to make sure that
the multi-company functionality is consistent.

* When the user is assigned to the multi-company group, all of the
  multi-company dependent objects will be listed with the company as suffix,
  in brackets.

* Provides a helper methods common to all models to help check multi-company
  consistency with other models that refer to or are refered by them.

* Ensures that the partner hierarchy is consistent company-wise.

* Fixes errors reported to Odoo:

- https://github.com/odoo/odoo/pull/23695
- https://github.com/odoo/odoo/pull/22851
- https://github.com/odoo/odoo/pull/22851
- https://github.com/odoo/odoo/issues/6276


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
