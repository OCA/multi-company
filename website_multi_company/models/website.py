# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class Website(models.Model):
    _inherit = 'website'

    @api.model
    def create(self, vals):
        record = super(Website, self).create(vals)
        record._sync_public_user()
        return record

    @api.multi
    def write(self, vals):
        res = super(Website, self).write(vals)
        self._sync_public_user()
        return res

    @api.multi
    def _sync_public_user(self):
        for record in self:
            if record.company_id == record.user_id.company_id:
                continue
            public_user = self.env.ref('base.public_user')
            if public_user.company_id != record.company_id:
                public_user = public_user.copy()
                public_user.company_id = record.company_id.id
            record.user_id = public_user.id
