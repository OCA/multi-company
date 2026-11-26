Receive purchases from a company of the group through the Incoming
transit of `purchase_stock_transit_receipt`, whatever their incoterm.

The validation of the seller's delivery validates the buyer's Transit
receipt with the shipped quantities and lots: the goods are in the
buyer's stock while in transit. The usual reception of the buyer's
warehouse waits for the goods to arrive, and only its validation sets
the received quantity of the purchase.

This complements *Sync the receipt with the delivery* of
`purchase_sale_stock_inter_company`, where the seller's delivery
validates the buyer's reception itself (dropship, or a warehouse that
does not record its receptions).
