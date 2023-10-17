from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    intercompany_in_type_id = fields.Many2one(
        "stock.picking.type",
        string="Intercompany Reception Type",
        help="Select the operation type that will be used to create the counterpart reception",
    )
    intercompany_out_type_id = fields.Many2one(
        "stock.picking.type",
        string="Intercompany Delivery Type",
        help="Select the operation type that will be used to create the counterpart delivery",
    )
    intercompany_picking_creation_mode = fields.Selection(
        selection=[
            ("in", "Reception Only"),
            ("out", "Delivery Only"),
            ("both", "Create Both"),
        ],
        string="Intercompany Picking Creation Mode",
        default="in",
        help="Select which intercompany pickings mode to use for this company\n"
        "  * Reception Only will create a reception on this company when a "
        "delivery is done on another company\n"
        "  * Delivery Only will create a delivery on this company when a "
        "reception is done on another company\n"
        "  * Create Both will create both a reception and a delivery on this "
        "company when a delivery or a reception is done on another company\n"
        "  * [Empty] will not create any picking on this company when a delivery "
        "or a reception is done on another company",
    )
