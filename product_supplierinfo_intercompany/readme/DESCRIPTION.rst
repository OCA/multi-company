This module allows to manage intercompany pricelist, to sell products
between companies in a multi-company environnement.

Choose any company as the seller company, and for it, define a pricelist and flag it as intercompany. For a product P and its cost C, whenever you add a price on that intercompany pricelist, all other companies will get a new supplierinfo for P at price C.

⚠ Tips:

In case that you have multiple intercompany pricelist or intercompany pricelist with price per quantity, we deeply recommand you to install the module product_supplierinfo_group_intercompany in order to be able to manage the supplier order correctly.
Indeed Odoo supplierinfo order it broken by design when you have price per quantity !
The module product_supplierinfo_group reintroduce the supplier group concept and manage sequence on the group to solve it.
The module product_supplierinfo_group_intercompany is a glue module between this two modules and add the possibility to define a global sequence on the intercompany pricelist that will be applied on generated supplier group
