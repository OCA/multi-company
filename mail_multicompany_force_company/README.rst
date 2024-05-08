

================================
Email Multi Company Force Server
================================

This module forces to use the mail server that is configured for the company in outgoing mail server configuration.
If there is a mail server without a company assigned, it will be used by all companies.
In case there is a mail server without company and your company has assigned a mail server, you will use your company's mail server

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fmulti--company-lightgray.png?logo=github
    :target: https://github.com/OCA/multi-company/tree/15.0/mail_multicompany
    :alt: OCA/multi-company

|badge1| |badge2| |badge3|

This module forces to use the mail server that is configured for the company in outgoing mail server configuration.

**Table of contents**

.. contents::
   :local:

Configuration
=============

* Install mail_multicompany module
* You don't need any additional steps to configure this module

Usage
=====

To use this module, you need:

Case 1
~~~~~~~

* Configure a mail server for your company
* Send a mail 

* If a user from another company tries to send a mail, that user never will be able to use your mail server

Case 2
~~~~~~~

* Configure a mail server without a company assigned
* Send a mail from any company

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/multi-company/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us to smash it by providing a detailed and welcomed
`feedback <https://github.com/OCA/multi-company/issues/new?body=module:%20mail_multicompany_force_company%0Aversion:%2015.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* iTecan

Contributors
~~~~~~~~~~~~

* iTecan <info@itecan.es>

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/multi-company <https://github.com/OCA/multi-company/tree/15.0>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.