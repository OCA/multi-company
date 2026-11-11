Assigns the current company to a new product when no company is set,
mirroring `partner_company_default` (OCA/partner-contact) for
`product.template`. Without this, a product created without an explicit
company ends up with a blank `company_ids` (shared across all companies),
which is rarely the intended result for a merchant in a multi-company
deployment.
