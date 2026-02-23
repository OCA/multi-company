#. [Company A] Create a sales order and use the previously created product.
#. [Company A] Confirm the sales order.
#. [Company A] The corresponding purchase order will have been created (confirm it if necessary).
#. [Company A] Complete the sales order delivery note.
#. [Company A] Create the RMA linked to the sales order.
#. [Company B] The sales order RMA will have been created automatically and will be linked.
#. The RMA from Company B will be confirmed automatically.
#. Reception picking for RMA A will have Transit Location defined as the destination location.
#. Reception picking for RMA B will have Transit Location defined as the origin location.
#. When validating the reception picking for RMA B, the reception picking for RMA A will be auto-done first.
#. When creating a delivery picking (return or replace) in RMA B, it will also be created in RMA A.
#. The RMA B delivery picking will have Transit Location as its destination location.
#. The RMA A delivery picking will have Transit Location as its origin location.
#. When validating the RMA B delivery picking, the RMA A delivery picking will be automatically done.
#. If RMA A is canceled, RMA B is automatically canceled.
#. If RMA B is canceled, RMA A is automatically canceled.
#. If RMA A is confirmed, RMA B is automatically confirmed.
#. If RMA B is confirmed, RMA A is automatically confirmed.
#. If RMA A is returned (using the return or replace button), RMA B is automatically returned.
#. If RMA B is returned (using the return or replace button), RMA A is automatically returned.
#. If RMA A is refunded, RMA B is automatically returned.
#. If RMA B is refunded, RMA A is automatically returned.
