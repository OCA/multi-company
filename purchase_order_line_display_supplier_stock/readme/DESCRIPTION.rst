This module displays, on each purchase order line, the stock available at the
supplier when that supplier is another company of the group (intercompany
purchases).

The displayed quantity is the **sum** of the stock across the supplier
company's warehouses that are flagged as visible, using the same warehouse flag
and the same global stock-field setting as
``sale_order_line_display_stock_per_warehouse``.

It also shows the supplier's first expected replenishment date for the product
when there is no stock, so the buying company can see it as early as the RFQ
stage.

