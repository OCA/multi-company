Odoo standard allows a pricelist to belong to **one company** or to **all companies** (when Company is left empty). There is no middle ground.

This module adds a **group of companies** option:

- Adds an **Available in Companies** field (many2many) to each pricelist.
- A pricelist can be shared with any subset of companies without exposing it to all.
- When **Company** is set, that company is automatically included in **Available in Companies**.
- When **Company** is empty, the pricelist remains globally accessible (standard behaviour) and the **Available in Companies** field is hidden.
- Security rules are updated so users can see pricelists where their company appears in **Available in Companies**.
- Pricelist items inherit the same visibility automatically.
