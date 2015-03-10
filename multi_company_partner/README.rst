.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

Multi Company Partner
=====================

This basic module aims to allow one customer to be shared among
    some of the sibling companies.

Standard Odoo limitation:
    one customer can be only private to one company or shared among
        all the sibling companies.

Note: This module add a new group who can read all the sibling companies
    information and can assign the customer to different companies
    when creating a new customer.
TODO:
    * eg, One salesperson belongs to two companies(A,B) at the same time.
        When the salesperson switch company from A to B, the users from
        company A cannot read the salesperson's information anymore.
    To solve this, we should change the salesperson to 

Installation
============

To install this module, you need to:

 * have basic modules installed (sale)

Configuration
=============

To configure this module, you need to:

 * No specific configuration needed.

Usage
=====
 A new field is introduced on partner form: Allowed companies under field 'System company'.
 everytime the salesperson creates a new customer,
 he can add allowed companies for this customer.The salesperson has to belong
 to the group "View all companies" to be able to see all the companies.

For further information, please visit:

 * https://www.odoo.com/forum/help-1

Known issues / Roadmap
======================


Credits
=======


Contributors
------------

* Alex Duan <alex.duan@elico-corp.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization
    whose mission is to support the collaborative development of Odoo features
        and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.