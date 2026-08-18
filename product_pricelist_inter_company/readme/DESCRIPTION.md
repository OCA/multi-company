Keeps `product.supplierinfo` in sync with inter-company pricelists.

Link a pricelist to one or more **Purchasing Companies** and the module handles:

- Adding a product rule → creates supplierinfo for every purchasing company.
- Updating the price → updates all linked supplierinfo records.
- Removing a rule → deletes the associated supplierinfo records.
- Adding / removing a purchasing company → creates / removes supplierinfo for all existing rules.

Managed supplierinfo records carry a **Pricelist Rule** back-link. Manually maintained records are never touched.
