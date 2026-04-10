This module allows to create counterpart transfers between companies
defined in multi-company configuration.

For each company, an **Intercompany Picking Creation Mode** and the
respective operation types can be configured. Based on this, when a
picking from company A to company B is processed, a new counterpart
picking in company B is created using the operation type defined in the
settings of that company.

The available creation modes are:

- **Reception Only** — create a reception in this company when a
  delivery is validated in another company (default).
- **Delivery Only** — create a delivery in this company when a reception
  is validated in another company. The counterpart is created on demand
  via the *Create Counterpart* button on the picking, or automatically
  via the *Create Delivery Counterpart Pickings* scheduled action.
- **Create Both** — create both a reception and a delivery depending on
  the direction of the validated transfer.
- **(empty)** — do not create any counterpart picking for this company.

Once a counterpart picking has been created, the origin picking is
locked to prevent modifications. Cancelling the origin picking also
cancels its counterpart(s).

Additional options (per destination company):

- **Sync Done Quantities** — copy the done quantities from the origin
  picking move lines to the counterpart move lines upon counterpart
  creation.
- **Share Lots / Serial Numbers** — make lots and serial numbers used on
  the origin picking company-independent (`company_id` set to empty) so
  they are immediately visible and reusable in the destination company
  without any duplication of traceability records.

**Caution:**

Package (colisage) synchronisation across companies is not handled by
this module. Moving packages between companies was using destructive
operations on the source side in the original
stock_intercompany_bidirectional and is has not been ported
