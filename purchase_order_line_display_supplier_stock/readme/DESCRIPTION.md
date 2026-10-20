This module allows to display stock levels in purchase
order line when supplier is another company of the group
(inter-company purchase orders).

The displayed quantity is the **sum** of chosen warehouses and locations and 
on the same global stock field setting from
`sale_order_line_display_stock_per_warehouse`.

The widget also shows the supplier's first expected replenishment date for the
product when there is no stock, so the buying company can see it as
early as the RFQ stage.
