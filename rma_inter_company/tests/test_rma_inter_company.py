# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form
from odoo.tools import mute_logger

from odoo.addons.rma_inter_company.tests.common import TestRmaInterCompanyBase


class TestRmaInterCompany(TestRmaInterCompanyBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.so_a.action_confirm()
        # Confirm PO Company A
        cls.po_a = cls.so_a._get_purchase_orders()
        cls.po_a.button_confirm()
        cls.so_a_picking = cls.po_a_picking = cls.po_a.picking_ids
        # Confirm SO Company B
        cls.so_b = cls.po_a.intercompany_sale_order_id
        cls.so_b_picking = cls.so_b.picking_ids
        # Validate OUT SO Company B
        cls.so_b_picking.button_validate()
        # Validate IN PO Company B
        cls.po_a_picking.button_validate()

    def test_misc_rma_intercompany_data(self):
        self.assertEqual(self.po_a_picking.state, "done")
        self.assertEqual(self.po_a_picking.company_id, self.company_a)
        self.assertEqual(self.so_a_picking.state, "done")
        self.assertEqual(self.so_a_picking.company_id, self.company_a)
        self.assertTrue(self.po_a_picking.intercompany_picking_id)
        intercompany_picking = self.po_a_picking.intercompany_picking_id
        self.assertEqual(intercompany_picking.company_id, self.company_b)
        self.assertEqual(intercompany_picking.sale_id, self.so_b)
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        self.assertEqual(rma_a.company_id, self.company_a)
        self.assertEqual(rma_a.order_id, self.so_a)
        self.assertTrue(rma_a.intercompany_rma_id)
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertEqual(rma_b.company_id, self.company_b)
        self.assertEqual(rma_b.order_id, self.so_b)
        self.assertEqual(rma_b.partner_id, self.company_a.partner_id)
        self.assertEqual(rma_b.state, "confirmed")

    def test_rma_intercompany_sync(self):
        operation_refund = self.env.ref("rma.rma_operation_refund")
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_b = rma_a.intercompany_rma_id
        rma_b.operation_id = operation_refund
        self.assertEqual(rma_b.operation_id, operation_refund)
        self.assertEqual(rma_a.operation_id, operation_refund)
        operation_replace = self.env.ref("rma.rma_operation_replace")
        rma_a.operation_id = operation_replace
        self.assertEqual(rma_a.operation_id, operation_replace)
        self.assertEqual(rma_b.operation_id, operation_replace)
        rma_b.write({"operation_id": False})
        self.assertFalse(rma_b.operation_id)
        self.assertFalse(rma_a.operation_id)

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_from_so_company_b(self):
        rma_b = self._create_rma(self.so_b, self.rma_user_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_a = rma_b.intercompany_origin_rma_id
        self.assertTrue(rma_a)
        self.assertEqual(rma_a.state, "confirmed")
        self.assertEqual(rma_a.intercompany_rma_id, rma_b)

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_cancel_company_b(self):
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_b.with_user(self.rma_user_b).action_cancel()
        self.assertEqual(rma_a.state, "cancelled")
        self.assertEqual(rma_b.state, "cancelled")
        rma_b.with_user(self.rma_user_b).action_draft()
        self.assertEqual(rma_a.state, "draft")
        self.assertEqual(rma_b.state, "draft")
        rma_b.with_user(self.rma_user_b).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        self.assertEqual(rma_b.state, "confirmed")

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_cancel_company_a(self):
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_a.with_user(self.rma_user_a).action_cancel()
        self.assertEqual(rma_a.state, "cancelled")
        self.assertEqual(rma_b.state, "cancelled")
        rma_a.with_user(self.rma_user_a).action_draft()
        self.assertEqual(rma_a.state, "draft")
        self.assertEqual(rma_b.state, "draft")
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        self.assertEqual(rma_b.state, "confirmed")

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_return_cancel_company_a(self):
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        self.assertEqual(rma_a_reception_picking.state, "assigned")
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_b_reception_picking.state, "assigned")
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        self.assertEqual(rma_a.reception_move_id.location_id, self.customer_loc)
        self.assertEqual(
            rma_a.reception_move_id.move_line_ids.location_id, self.customer_loc
        )
        self.assertEqual(
            rma_a.reception_move_id.location_dest_id, self.intercompany_location
        )
        self.assertEqual(
            rma_a.reception_move_id.move_line_ids.location_dest_id,
            self.intercompany_location,
        )
        self.assertEqual(
            rma_b.reception_move_id.location_id, self.intercompany_location
        )
        self.assertEqual(
            rma_b.reception_move_id.move_line_ids.location_id,
            self.intercompany_location,
        )
        self.assertEqual(
            rma_b.reception_move_id.location_dest_id, self.warehouse_b.rma_loc_id
        )
        self.assertEqual(
            rma_b.reception_move_id.move_line_ids.location_dest_id,
            self.warehouse_b.rma_loc_id,
        )
        # Return rma A
        res = rma_a.action_return()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard = wizard_form.save()
        wizard.with_user(self.rma_user_a).action_deliver()
        self.assertEqual(rma_b.state, "waiting_return")
        rma_b_delivery_picking = rma_b.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        self.assertEqual(rma_a.state, "waiting_return")
        rma_a_delivery_picking = rma_a.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        # location data
        self.assertEqual(
            rma_b.delivery_move_ids.location_id, self.warehouse_b.rma_loc_id
        )
        self.assertEqual(
            rma_b.delivery_move_ids.move_line_ids.location_id,
            self.warehouse_b.rma_loc_id,
        )
        self.assertEqual(
            rma_b.delivery_move_ids.location_dest_id, self.intercompany_location
        )
        self.assertEqual(
            rma_b.delivery_move_ids.move_line_ids.location_dest_id,
            self.intercompany_location,
        )
        self.assertEqual(
            rma_a.delivery_move_ids.location_id, self.intercompany_location
        )
        self.assertEqual(
            rma_a.delivery_move_ids.move_line_ids.location_id,
            self.intercompany_location,
        )
        self.assertEqual(rma_a.delivery_move_ids.location_dest_id, self.customer_loc)
        self.assertEqual(
            rma_a.delivery_move_ids.move_line_ids.location_dest_id, self.customer_loc
        )
        # cancel picking
        rma_a_delivery_picking.with_user(self.rma_user_a).action_cancel()
        self.assertEqual(rma_a_delivery_picking.state, "cancel")
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        self.assertEqual(rma_a.state, "received")
        self.assertEqual(rma_b.state, "waiting_return")
        rma_b_delivery_picking.with_user(self.rma_user_b).action_cancel()
        self.assertEqual(rma_b_delivery_picking.state, "cancel")
        self.assertEqual(rma_b.state, "received")

    def test_rma_intercompany_reception_company_b(self):
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertEqual(rma_b.state, "confirmed")
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        rma_b_reception_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_return_cancel_company_b(self):
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        # Return rma A
        res = rma_a.action_return()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard = wizard_form.save()
        wizard.with_user(self.rma_user_a).action_deliver()
        self.assertEqual(rma_b.state, "waiting_return")
        rma_b_delivery_picking = rma_b.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        self.assertEqual(rma_a.state, "waiting_return")
        rma_a_delivery_picking = rma_a.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        rma_b_delivery_picking.with_user(self.rma_user_b).action_cancel()
        self.assertEqual(rma_a_delivery_picking.state, "cancel")
        self.assertEqual(rma_b_delivery_picking.state, "cancel")
        self.assertEqual(rma_a.state, "received")
        self.assertEqual(rma_b.state, "received")

    def test_rma_intercompany_full_company_b(self):
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_a = rma_a.with_user(self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(len(self.so_a.order_line), 1)
        self.assertEqual(rma_a.state, "confirmed")
        self.assertEqual(rma_a.warehouse_id, self.warehouse_a)
        rma_b = rma_a.intercompany_rma_id.with_user(self.rma_user_b)
        self.assertTrue(rma_b)
        self.assertEqual(len(self.so_b.order_line), 1)
        self.assertEqual(rma_b.company_id, self.company_b)
        self.assertEqual(rma_b.partner_id, self.company_a.partner_id)
        self.assertEqual(rma_b.warehouse_id, self.warehouse_b)
        self.assertEqual(rma_b.location_id, self.warehouse_b.rma_loc_id)
        self.assertEqual(rma_b.intercompany_origin_rma_id, rma_a)
        self.assertEqual(rma_b.state, "confirmed")
        self.assertEqual(rma_b.order_id, self.so_b)
        self.assertEqual(
            rma_b.reception_move_id.location_id, self.intercompany_location
        )
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_a.intercompany_rma_id, rma_b)
        self.assertEqual(
            rma_a.reception_move_id.location_dest_id, self.intercompany_location
        )
        self.assertTrue(rma_a.reception_move_id.origin_returned_move_id)
        self.assertEqual(rma_b_reception_picking.state, "assigned")
        self.assertEqual(
            rma_b_reception_picking.picking_type_id, self.warehouse_b.rma_in_type_id
        )
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        self.assertEqual(
            rma_a_reception_picking.picking_type_id, self.warehouse_a.rma_in_type_id
        )
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        self.assertEqual(len(self.so_a.order_line), 1)
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        self.assertEqual(len(self.so_b.order_line), 1)
        # Return rma B
        res = rma_b.action_return()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard = wizard_form.save()
        wizard.with_user(self.rma_user_b).action_deliver()
        self.assertEqual(rma_b.state, "waiting_return")
        self.assertEqual(
            rma_b.delivery_move_ids.location_dest_id, self.intercompany_location
        )
        rma_b_delivery_picking = rma_b.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        self.assertEqual(
            rma_b_delivery_picking.picking_type_id, self.warehouse_b.rma_out_type_id
        )
        self.assertEqual(rma_a.state, "waiting_return")
        self.assertEqual(
            rma_a.delivery_move_ids.location_id, self.intercompany_location
        )
        rma_a_delivery_picking = rma_a.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        self.assertEqual(
            rma_a_delivery_picking.picking_type_id, self.warehouse_a.rma_out_type_id
        )
        rma_b_delivery_picking.move_ids.quantity = 1
        rma_b_delivery_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_b_delivery_picking.state, "done")
        self.assertEqual(rma_b.state, "returned")
        self.assertEqual(len(self.so_b.order_line), 1)
        self.assertEqual(rma_a_delivery_picking.state, "done")
        self.assertEqual(rma_a.state, "returned")
        self.assertEqual(len(self.so_a.order_line), 1)
        # new rma
        self.company_a.rma_new_rma_button_from_rma = True
        self.company_b.rma_new_rma_button_from_rma = True
        operation_refund = self.env.ref("rma.rma_operation_refund")
        res = rma_b.action_create_rma()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard_form.operation_id = operation_refund
        wizard = wizard_form.save()
        rma_b_extra = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        self.assertEqual(rma_b_extra.state, "confirmed")
        self.assertEqual(rma_b_extra.company_id, self.company_b)
        self.assertEqual(rma_b_extra.operation_id, operation_refund)
        self.assertFalse(rma_b_extra.order_id)
        self.assertEqual(rma_b_extra.move_id, rma_b.delivery_move_ids)
        self.assertTrue(rma_b_extra.intercompany_rma_id)
        rma_a_extra = rma_b_extra.intercompany_rma_id
        self.assertEqual(rma_a_extra.state, "confirmed")
        self.assertEqual(rma_a_extra.company_id, self.company_a)
        self.assertEqual(rma_a_extra.operation_id, operation_refund)
        self.assertEqual(rma_a_extra.intercompany_origin_rma_id, rma_b_extra)
        self.assertFalse(rma_a_extra.order_id)
        self.assertEqual(rma_a_extra.move_id, rma_a.delivery_move_ids)

    def test_rma_intercompany_full_company_a(self):
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_a = rma_a.with_user(self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(len(self.so_a.order_line), 1)
        self.assertEqual(rma_a.state, "confirmed")
        self.assertEqual(rma_a.warehouse_id, self.warehouse_a)
        rma_b = rma_a.intercompany_rma_id.with_user(self.rma_user_b)
        self.assertTrue(rma_b)
        self.assertEqual(len(self.so_b.order_line), 1)
        self.assertEqual(rma_b.company_id, self.company_b)
        self.assertEqual(rma_b.partner_id, self.company_a.partner_id)
        self.assertEqual(rma_b.warehouse_id, self.warehouse_b)
        self.assertEqual(rma_b.location_id, self.warehouse_b.rma_loc_id)
        self.assertEqual(rma_b.intercompany_origin_rma_id, rma_a)
        self.assertEqual(rma_b.state, "confirmed")
        self.assertEqual(rma_b.order_id, self.so_b)
        self.assertEqual(
            rma_b.reception_move_id.location_id, self.intercompany_location
        )
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_a.intercompany_rma_id, rma_b)
        self.assertEqual(
            rma_a.reception_move_id.location_dest_id, self.intercompany_location
        )
        self.assertTrue(rma_a.reception_move_id.origin_returned_move_id)
        self.assertEqual(rma_b_reception_picking.state, "assigned")
        self.assertEqual(
            rma_b_reception_picking.picking_type_id, self.warehouse_b.rma_in_type_id
        )
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        self.assertEqual(
            rma_a_reception_picking.picking_type_id, self.warehouse_a.rma_in_type_id
        )
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        self.assertEqual(len(self.so_a.order_line), 1)
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        self.assertEqual(len(self.so_b.order_line), 1)
        # Return rma A
        res = rma_a.action_return()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard = wizard_form.save()
        wizard.with_user(self.rma_user_a).action_deliver()
        self.assertEqual(rma_a.state, "waiting_return")
        self.assertEqual(rma_b.state, "waiting_return")
        self.assertEqual(
            rma_b.delivery_move_ids.location_dest_id, self.intercompany_location
        )
        rma_b_delivery_picking = rma_b.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        self.assertEqual(
            rma_b_delivery_picking.picking_type_id, self.warehouse_b.rma_out_type_id
        )
        self.assertEqual(
            rma_a.delivery_move_ids.location_id, self.intercompany_location
        )
        rma_a_delivery_picking = rma_a.delivery_move_ids.picking_id
        self.assertEqual(rma_b_delivery_picking.state, "assigned")
        self.assertEqual(
            rma_a_delivery_picking.picking_type_id, self.warehouse_a.rma_out_type_id
        )
        rma_a_delivery_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_delivery_picking.state, "done")
        self.assertEqual(rma_a.state, "returned")
        self.assertEqual(len(self.so_a.order_line), 1)
        self.assertEqual(rma_b_delivery_picking.state, "done")
        self.assertEqual(rma_b.state, "returned")
        self.assertEqual(len(self.so_b.order_line), 1)
        # new rma
        self.company_a.rma_new_rma_button_from_rma = True
        self.company_b.rma_new_rma_button_from_rma = True
        operation_refund = self.env.ref("rma.rma_operation_refund")
        res = rma_a.action_create_rma()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard_form.operation_id = operation_refund
        wizard = wizard_form.save()
        rma_a_extra = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        self.assertEqual(rma_a_extra.state, "confirmed")
        self.assertEqual(rma_a_extra.company_id, self.company_a)
        self.assertEqual(rma_a_extra.operation_id, operation_refund)
        self.assertFalse(rma_a_extra.order_id)
        self.assertEqual(rma_a_extra.move_id, rma_a.delivery_move_ids)
        self.assertTrue(rma_a_extra.intercompany_rma_id)
        rma_b_extra = rma_a_extra.intercompany_rma_id
        self.assertEqual(rma_b_extra.state, "confirmed")
        self.assertEqual(rma_b_extra.company_id, self.company_b)
        self.assertEqual(rma_b_extra.operation_id, operation_refund)
        self.assertEqual(rma_b_extra.intercompany_origin_rma_id, rma_a_extra)
        self.assertFalse(rma_b_extra.order_id)
        self.assertEqual(rma_b_extra.move_id, rma_b.delivery_move_ids)

    def test_rma_intercompany_replace_full_company_b(self):
        self._update_available_quantity(
            self.product_2, self.warehouse_b.lot_stock_id, 1
        )
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_a = rma_a.with_user(self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        self.assertEqual(
            rma_a_reception_picking.picking_type_id, self.warehouse_a.rma_in_type_id
        )
        rma_a_reception_picking.move_ids.quantity = 1
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        self.assertEqual(len(self.so_a.order_line), 1)
        rma_b = rma_a.intercompany_rma_id.with_user(self.rma_user_b)
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        self.assertEqual(len(self.so_b.order_line), 1)
        # Replace rma B
        res = rma_b.action_replace()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard_form.product_id = self.product_2
        wizard = wizard_form.save()
        wizard.with_user(self.rma_user_b).action_deliver()
        self.assertEqual(rma_b.state, "waiting_replacement")
        self.assertEqual(
            rma_b.delivery_move_ids.location_dest_id, self.intercompany_location
        )
        self.assertEqual(rma_b.delivery_move_ids.product_id, self.product_2)
        rma_b_delivery_picking = rma_b.delivery_move_ids.picking_id
        self.assertEqual(
            rma_b_delivery_picking.picking_type_id, self.warehouse_b.rma_out_type_id
        )
        self.assertEqual(rma_a.state, "waiting_replacement")
        self.assertEqual(
            rma_a.delivery_move_ids.location_id, self.intercompany_location
        )
        self.assertEqual(rma_a.delivery_move_ids.product_id, self.product_2)
        rma_a_delivery_picking = rma_a.delivery_move_ids.picking_id
        self.assertEqual(rma_a_delivery_picking.state, "assigned")
        self.assertEqual(
            rma_a_delivery_picking.picking_type_id, self.warehouse_a.rma_out_type_id
        )
        self.assertEqual(rma_b_delivery_picking.state, "confirmed")
        rma_b_delivery_picking.move_ids.quantity = 1
        rma_b_delivery_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_b_delivery_picking.state, "done")
        self.assertEqual(rma_b.state, "replaced")
        self.assertEqual(len(self.so_b.order_line), 1)
        self.assertEqual(rma_a_delivery_picking.state, "done")
        self.assertEqual(rma_a.state, "replaced")
        self.assertEqual(len(self.so_a.order_line), 1)

    def test_rma_intercompany_replace_full_company_a(self):
        self.operation.action_create_delivery = "manual_on_confirm"
        self._update_available_quantity(
            self.product_2, self.warehouse_b.lot_stock_id, 1
        )
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_a = rma_a.with_user(self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        self.assertEqual(
            rma_a_reception_picking.picking_type_id, self.warehouse_a.rma_in_type_id
        )
        rma_a_reception_picking.move_ids.quantity = 1
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        self.assertEqual(len(self.so_a.order_line), 1)
        rma_b = rma_a.intercompany_rma_id.with_user(self.rma_user_b)
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(
            rma_b_reception_picking.picking_type_id, self.warehouse_b.rma_in_type_id
        )
        self.assertEqual(rma_b.state, "received")
        self.assertEqual(len(self.so_b.order_line), 1)
        # Replace rma A
        res = rma_a.action_replace()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard_form.product_id = self.product_2
        wizard = wizard_form.save()
        wizard.with_user(self.rma_user_a).action_deliver()
        self.assertEqual(rma_b.state, "waiting_replacement")
        self.assertEqual(
            rma_b.delivery_move_ids.location_dest_id, self.intercompany_location
        )
        self.assertEqual(rma_b.delivery_move_ids.product_id, self.product_2)
        rma_b_delivery_picking = rma_b.delivery_move_ids.picking_id
        self.assertEqual(
            rma_b_delivery_picking.picking_type_id, self.warehouse_b.rma_out_type_id
        )
        self.assertEqual(rma_a.state, "waiting_replacement")
        self.assertEqual(
            rma_a.delivery_move_ids.location_id, self.intercompany_location
        )
        self.assertEqual(rma_a.delivery_move_ids.product_id, self.product_2)
        rma_a_delivery_picking = rma_a.delivery_move_ids.picking_id
        self.assertEqual(rma_a_delivery_picking.state, "assigned")
        self.assertEqual(
            rma_a_delivery_picking.picking_type_id, self.warehouse_a.rma_out_type_id
        )
        self.assertEqual(rma_b_delivery_picking.state, "confirmed")
        rma_b_delivery_picking.move_ids.quantity = 1
        rma_b_delivery_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_b_delivery_picking.state, "done")
        self.assertEqual(rma_b.state, "replaced")
        self.assertEqual(len(self.so_b.order_line), 1)
        self.assertEqual(rma_a_delivery_picking.state, "done")
        self.assertEqual(rma_a.state, "replaced")
        self.assertEqual(len(self.so_a.order_line), 1)

    def test_rma_intercompany_new_rma_company_a(self):
        self.company_a.rma_new_rma_button_from_rma = True
        self.company_b.rma_new_rma_button_from_rma = True
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        # Return rma A
        res = rma_a.action_return()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard = wizard_form.save()
        wizard.with_user(self.rma_user_a).action_deliver()
        self.assertEqual(rma_a.state, "waiting_return")
        self.assertEqual(rma_b.state, "waiting_return")
        rma_a.delivery_move_ids.picking_id.button_validate()
        self.assertEqual(rma_a.state, "returned")
        self.assertEqual(rma_b.state, "returned")
        # new rma (from rma a)
        res = rma_a.action_create_rma()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard = wizard_form.save()
        new_rma_a = wizard.with_user(self.rma_user_a).create_rma()
        self.assertTrue(new_rma_a)
        self.assertEqual(new_rma_a.state, "confirmed")
        new_rma_b = rma_b.delivery_move_ids.rma_ids
        self.assertTrue(new_rma_b)
        self.assertEqual(new_rma_b.state, "confirmed")

    def test_rma_intercompany_new_rma_company_b(self):
        self.company_a.rma_new_rma_button_from_rma = True
        self.company_b.rma_new_rma_button_from_rma = True
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        # Return rma B
        res = rma_b.action_return()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard = wizard_form.save()
        wizard.with_user(self.rma_user_b).action_deliver()
        self.assertEqual(rma_b.state, "waiting_return")
        self.assertEqual(rma_a.state, "waiting_return")
        rma_b.delivery_move_ids.picking_id.button_validate()
        self.assertEqual(rma_b.state, "returned")
        self.assertEqual(rma_a.state, "returned")
        # new rma (from rma b)
        res = rma_b.action_create_rma()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard = wizard_form.save()
        new_rma_b = wizard.with_user(self.rma_user_b).create_rma()
        self.assertTrue(new_rma_b)
        self.assertEqual(new_rma_b.state, "confirmed")
        new_rma_a = rma_a.delivery_move_ids.rma_ids
        self.assertTrue(new_rma_a)
        self.assertEqual(new_rma_a.state, "confirmed")

    def test_rma_intercompany_refund_without_invoice_company_a(self):
        self.operation.action_create_refund = "manual_after_receipt"
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        # Refund Company A
        rma_a.with_user(self.rma_user_a).action_refund_without_invoice()
        self.assertEqual(rma_a.state, "refunded")
        self.assertFalse(rma_a.refund_id)
        self.assertEqual(rma_b.state, "refunded")
        self.assertFalse(rma_b.refund_id)

    def test_rma_intercompany_refund_without_invoice_company_b(self):
        self.operation.action_create_refund = "manual_after_receipt"
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        # Refund Company B
        rma_b.with_user(self.rma_user_b).action_refund_without_invoice()
        self.assertEqual(rma_b.state, "refunded")
        self.assertFalse(rma_b.refund_id)
        self.assertEqual(rma_a.state, "refunded")
        self.assertFalse(rma_a.refund_id)

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_refund_company_a(self):
        self.operation.action_create_refund = "manual_after_receipt"
        self.so_a._create_invoices()
        self.so_b._create_invoices()
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        # Refund Company A
        rma_a.with_user(self.rma_user_a).action_refund()
        self.assertEqual(rma_a.state, "refunded")
        self.assertTrue(rma_a.refund_id)
        self.assertEqual(rma_a.refund_id.company_id, self.company_a)
        self.assertEqual(rma_b.state, "refunded")
        self.assertTrue(rma_b.refund_id)
        self.assertEqual(rma_b.refund_id.company_id, self.company_b)

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_refund_company_b(self):
        self.operation.action_create_refund = "manual_after_receipt"
        self.so_a._create_invoices()
        self.so_b._create_invoices()
        rma_a = self._create_rma(self.so_a, self.rma_user_a)
        rma_a.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma_a.state, "confirmed")
        rma_b = rma_a.intercompany_rma_id
        self.assertTrue(rma_b)
        self.assertEqual(rma_b.state, "confirmed")
        rma_a_reception_picking = rma_a.reception_move_id.picking_id
        rma_a_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_a_reception_picking.state, "done")
        self.assertEqual(rma_a.state, "received")
        rma_b_reception_picking = rma_b.reception_move_id.picking_id
        self.assertEqual(rma_b_reception_picking.state, "done")
        self.assertEqual(rma_b.state, "received")
        # Refund Company B
        rma_b.with_user(self.rma_user_b).action_refund()
        self.assertEqual(rma_b.state, "refunded")
        self.assertTrue(rma_b.refund_id)
        self.assertEqual(rma_b.refund_id.company_id, self.company_b)
        self.assertEqual(rma_a.state, "refunded")
        self.assertTrue(rma_a.refund_id)
        self.assertEqual(rma_a.refund_id.company_id, self.company_a)

    def test_rma_not_intercompany_company_a(self):
        self._update_available_quantity(
            self.product_2, self.warehouse_a.lot_stock_id, 1
        )
        order_form = Form(self.env["sale.order"].with_company(self.company_a))
        order_form.partner_id = self.customer
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product_2
        so = order_form.save()
        so.action_confirm()
        self.assertEqual(so.state, "sale")
        picking = so.picking_ids
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        rma = self._create_rma(so, self.rma_user_a)
        rma = rma.with_user(self.rma_user_a)
        rma.with_user(self.rma_user_a).action_confirm()
        self.assertEqual(rma.company_id, self.company_a)
        self.assertEqual(rma.state, "confirmed")
        self.assertEqual(rma.warehouse_id, self.warehouse_a)
        self.assertEqual(rma.location_id, self.warehouse_a.rma_loc_id)
        self.assertEqual(rma.state, "confirmed")
        self.assertEqual(rma.reception_move_id.location_id, self.customer_loc)
        self.assertEqual(
            rma.reception_move_id.location_dest_id, self.warehouse_a.rma_loc_id
        )
        rma_reception_picking = rma.reception_move_id.picking_id
        self.assertEqual(
            rma_reception_picking.picking_type_id, self.warehouse_a.rma_in_type_id
        )
        rma_reception_picking.with_user(self.rma_user_a).button_validate()
        self.assertEqual(rma_reception_picking.state, "done")
        self.assertEqual(rma.state, "received")

    def test_rma_not_intercompany_company_b(self):
        self._update_available_quantity(
            self.product_2, self.warehouse_b.lot_stock_id, 1
        )
        order_form = Form(self.env["sale.order"].with_company(self.company_b))
        order_form.partner_id = self.customer
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product_2
        so = order_form.save()
        so.action_confirm()
        self.assertEqual(so.state, "sale")
        picking = so.picking_ids
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        rma = self._create_rma(so, self.rma_user_b)
        rma = rma.with_user(self.rma_user_b)
        rma.with_user(self.rma_user_b).action_confirm()
        self.assertEqual(rma.company_id, self.company_b)
        self.assertEqual(rma.state, "confirmed")
        self.assertEqual(rma.warehouse_id, self.warehouse_b)
        self.assertEqual(rma.location_id, self.warehouse_b.rma_loc_id)
        self.assertEqual(rma.state, "confirmed")
        self.assertEqual(rma.reception_move_id.location_id, self.customer_loc)
        self.assertEqual(
            rma.reception_move_id.location_dest_id, self.warehouse_b.rma_loc_id
        )
        rma_reception_picking = rma.reception_move_id.picking_id
        self.assertEqual(
            rma_reception_picking.picking_type_id, self.warehouse_b.rma_in_type_id
        )
        rma_reception_picking.with_user(self.rma_user_b).button_validate()
        self.assertEqual(rma_reception_picking.state, "done")
        self.assertEqual(rma.state, "received")
