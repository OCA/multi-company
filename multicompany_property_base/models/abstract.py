# Copyright 2017 Creu Blanca
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import MissingError


class ModelProperty(models.AbstractModel):
    _name = 'model.property'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        readonly=True
    )

    @api.multi
    def _compute_property_fields(self):
        raise MissingError(_('It must be redefined'))

    # This is the function we will extend in order to generate the information
    @api.multi
    def get_property_fields(self, object, properties):
        raise MissingError(_('It must be redefined'))

    def set_property(self, object, fieldname, value, properties):
        properties.with_context(
            force_company=self.company_id.id).sudo().set_multi(
            fieldname, object._name, {object.id: value})

    def get_property_value(self, field, object, prop_obj):
        value = prop_obj.get(field, object._name, (object._name + ',%s') %
                             object.id)
        if value:
            if isinstance(value, list):
                return value[0]
            else:
                return value
        value = prop_obj.get(field, object._name)
        if value:
            if isinstance(value, list):
                return value[0]
            else:
                return value
        return False

    @api.multi
    def get_property_fields_list(self):
        return []
