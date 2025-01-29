Implementation
~~~~~~~~~~~~~~

Multi Company Abstract
----------------------

The ``multi.company.abstract`` model is meant to be inherited by any model that
wants to implement multi-company functionality. The logic does not require a
pre-existing company field on the inheriting model, but will not be affected
if one does exist.

When inheriting the ``multi.company.abstract`` model, you must take care that
it is the first model listed in the ``_inherit`` array

.. code-block:: python

   class ProductTemplate(models.Model):
       _inherit = ["multi.company.abstract", "product.template"]
       _name = "product.template"
       _description = "Product Template (Multi-Company)"

The following fields are provided by ``multi.company.abstract``:

* ``company_ids`` - All of the companies that this record belongs to. This is a
  special ``res.company.assignment`` view, which allows for the circumvention of
  standard cross-company security policies. These policies would normally
  restrict a user from seeing another company unless it is currently operating
  under that company. Be aware of apples to oranges issues when comparing the
  records from this field against actual company records.
* ``company_id`` - Passes through a singleton company based on the current user,
  and the allowed companies for the record.

Hooks
-----

A generic ``fill_company_ids`` hook is provided, to be used in submodules'
``post_init_hook``, which will convert the ``company_id`` field to a
``company_ids`` field, respecting previous company assignments.

It will unfortunately not work in every circumstance, but it cuts out
significant boilerplate when relevant.

.. code-block:: python

   from odoo.addons.base_multi_company import hooks

   def post_init_hook(cr, registry):
       hooks.fill_company_ids(
           cr,
           'product.template',
       )

Other hooks are deprecated and no longer needed.
