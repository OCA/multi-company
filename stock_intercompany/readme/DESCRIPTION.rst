This module allows to create counterpart transfers between companies defined in
multi-company configuration.

For each company 'intercompany operation type' field must be set. Based on
this, when a picking from company A to company B is processed, a new incoming
picking in company B is created, using the picking type defined in the settings
of that company.

Caution:

currently, lots and packages are not handled.
