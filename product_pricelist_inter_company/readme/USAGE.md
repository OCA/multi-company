Once configured, the module works automatically:

- When a product rule is added to the pricelist, a vendor price entry is created for each purchasing company, with the vendor set to the pricelist's company partner.
- When the price of a rule is updated, all linked vendor price entries are updated accordingly.
- When a rule is deleted, its linked vendor price entries are removed.
- When a purchasing company is added to the pricelist, vendor price entries are created for all existing product rules.
- When a purchasing company is removed, its vendor price entries are deleted.

Vendor price entries managed by this module carry a **Pricelist Rule** link (optionally visible in Vendor List). Manually created vendor price entries without this back-link are never modified or deleted by the module.
