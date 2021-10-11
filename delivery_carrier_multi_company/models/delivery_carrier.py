# Copyright 2021 Acsone SA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = ["multi.company.abstract", "delivery.carrier"]
    _name = "delivery.carrier"
    _description = "Delivery Carrier (Multi-Company)"

    company_ids = fields.Many2many(
        related="product_id.company_ids",
        comodel_name="res.company",
        store=True,
        relation="delivery_carrier_res_company_rel_2",
        column1="carrier_id",
        column2="res_company_id",
        ondelete="restrict",
    )
