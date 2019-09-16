# coding: utf-8
# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class ResCompanyCategory(models.Model):
    _name = 'res.company.category'
    _order = 'complete_name'

    _TYPE_SELECTION = [
        ('normal', 'Normal'),
        ('view', 'View'),
    ]

    # Fields Section
    name = fields.Char(string='Name', required=True)

    type = fields.Selection(
        string='Type', selection=_TYPE_SELECTION,
        required=True, default='normal')

    parent_id = fields.Many2one(
        string='Parent Category', comodel_name='res.company.category',
        domain=[('type', '=', 'view')])

    child_ids = fields.One2many(
        string='Category Childs', comodel_name='res.company.category',
        inverse_name='parent_id')

    company_ids = fields.One2many(
        string='Companies', comodel_name='res.company',
        inverse_name='category_id')

    company_qty = fields.Integer(
        string='Companies Quantity', compute='_compute_company_qty',
        store=True)

    complete_name = fields.Char(
        string='Complete Name', compute='_compute_complete_name', store=True)

    # Compute Section
    @api.multi
    @api.depends('parent_id.complete_name', 'name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (
                    category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    @api.multi
    @api.depends('company_ids.category_id', 'child_ids.company_qty')
    def _compute_company_qty(self):
        for category in self:
            if category.type == 'normal':
                category.company_qty = len(category.company_ids)
            else:
                category.company_qty = sum(
                    category.mapped('child_ids.company_qty'))
