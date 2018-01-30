# Copyright 2017 Creu Blanca
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models, api


class Partner(models.Model):
    _inherit = 'res.partner'

    property_ids = fields.One2many(
        comodel_name='res.partner.property',
        compute='_compute_properties',
        inverse='_inverse_properties',
        string='Properties'
    )

    @api.multi
    def _inverse_properties(self):
        """ Hack here: We do not really store any value here.
        But this allows us to have the fields of the transient
        model editable. """
        return

    @api.multi
    def _compute_properties(self):
        for record in self:
            property_obj = self.env['res.partner.property']
            values = []
            companies = self.env['res.company'].search([])
            for company in companies:
                val = property_obj.create({
                    'partner_id': record.id,
                    'company_id': company.id
                })
                values.append(val.id)
            record.property_ids = values


class PartnerProperty(models.TransientModel):
    _name = 'res.partner.property'
    _inherit = 'model.property'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner'
    )

    @api.multi
    def _compute_property_fields(self):
        for rec in self:
            rec.get_property_fields(rec.partner_id,
                                    rec.env['ir.property'].with_context(
                                        force_company=rec.company_id.id))

    @api.multi
    def get_property_fields(self, object, properties):
        """ This method must be redefined by modules that
        introduce property fields in the res.partner model """
        return

    @api.multi
    def write(self, vals):
        prop_obj = self.env['ir.property'].with_context(
            force_company=self.company_id.id)
        p_fields = self.get_property_fields_list()
        for field in p_fields:
            if field in vals:
                for rec in self:
                    self.set_property(rec.partner_id, field,
                                      vals[field], prop_obj)
        return super(PartnerProperty, self).write(vals)
