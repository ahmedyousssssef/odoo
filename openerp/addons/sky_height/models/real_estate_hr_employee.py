# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.constrains('user_id')
    def check_related_user(self):
        for val in self:
            if val.user_id:
                usr_ids = self.search([('user_id', '=', val.user_id.id)])
                if len(usr_ids) > 1:
                    raise ValidationError(_('Sorry this related user is already exist with another employee'))
