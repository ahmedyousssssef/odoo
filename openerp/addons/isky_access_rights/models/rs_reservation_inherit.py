# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError

class RsReservationInherit(models.Model):
    _inherit = 'rs.reservation'

    def _default_check_is_sales_head(self):
        if self.env.user.has_group('sky_height.sales_head_user'):
            return True
        else:
            return False

    def _check_is_salesperson(self):
        for rec in self:
            rec.is_saleperson = True if self.env.user.has_group('base.group_sale_salesman') or self.env.user.has_group(
                'sky_height.sale_team_leader_group') else False
            return rec.is_saleperson

    is_saleperson = fields.Boolean(compute='_check_is_salesperson', default=_check_is_salesperson)
    is_sales_head = fields.Boolean(compute='_check_is_sales_head', default=_default_check_is_sales_head)

    def _check_is_sales_head(self):
        for rec in self:
            rec.is_sales_head = True if self.env.user.has_group('sky_height.sales_head_user') else False


    # Override cancel to empty the reserved salesperon field
    @api.multi
    def cancel(self):
        super(RsReservationInherit, self).cancel()
        for rec in self:
            for each_unit in rec.unit_ids:
                each_unit.write({
                    'reserved_user_ids': False
                })

    @api.multi
    def button_in_progress(self):
        super(RsReservationInherit, self).button_in_progress()
        for rec in self:
            for each_unit in rec.unit_ids:
                user_ids = rec.user_ids.ids if rec.user_ids else []
                each_unit.write({
                    'reserved_user_ids': [(6, 0, user_ids)]
                })