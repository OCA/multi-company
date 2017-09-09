.. image:: https://img.shields.io/badge/licence-lgpl--3-blue.svg
   :target: http://www.gnu.org/licenses/LGPL-3.0-standalone.html
   :alt: License: LGPL-3

==================
Multi Company Base
==================

This module provides an abstract model to be inherited by models that need
to implement multi-company functionality.

No direct functionality is provided by this module.

Implementation
==============

Multi Company Abstract
----------------------

The `multi.company.abstract` model is meant to be inherited by any model that
wants to implement multi-company functionality. The logic does not require a
pre-existing company field on the inheriting model, but will not be affected
if one does exist.

When inheriting the `multi.company.abstract` model, you must take care that
it is the first model listed in the `_inherit` array

.. code-block:: python

   class ProductTemplate(models.Model):
       _inherit = ["multi.company.abstract", "product.template"]
       _name = "product.template"
       _description = "Product Template (Multi-Company)"

The following fields are provided by `multi.company.abstract`:

* `company_ids` - All of the companies that this record belongs to. This is a
  special `res.company.assignment` view, which allows for the circumvention of
  standard cross-company security policies. These policies would normally
  restrict a user from seeing another company unless it is currently operating
  under that company. Be aware of apples to oranges issues when comparing the
  records from this field against actual company records.
* `company_id` - Passes through a singleton company based on the current user,
  and the allowed companies for the record.

Hooks
-----

A generic `post_init_hook` and `uninstall_hook` is provided, which will alter
a pre-existing single-company security rule to be multi-company aware.

These hooks will unfortunately not work in every circumstance, but they cut out
significant boilerplate when relevant.

.. code-block:: python

   import logging

   _logger = logging.getLogger(__name__)

   try:
       from odoo.addons.base_multi_company import hooks
   except ImportError:
       _logger.info('Cannot find `base_multi_company` module in addons path.')


   def post_init_hook(cr, registry):
       hooks.post_init_hook(
           cr,
           'product.product_comp_rule',
           'product.template',
       )


   def uninstall_hook(cr, registry):
       hooks.uninstall_hook(
           cr,
           'product.product_comp_rule',
       )

A module implementing these hooks would need to first identify the proper rule
for the record (`product.product_comp_rule` in the above example).

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/133/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/multi-company/issues>`_.
In case of trouble, please check there if your issue has already been reported. 
If you spotted it first, help us smash it by providing detailed and welcomed 
feedback.

Credits
=======

Images
------

* Odoo Community Association: 
  `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Dave Lasley <dave@laslabs.com>
* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* Laurent Mignon <laurent.mignon@acsone.eu>
* Cédric Pigeon <cedric.pigeon@acsone.eu>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
