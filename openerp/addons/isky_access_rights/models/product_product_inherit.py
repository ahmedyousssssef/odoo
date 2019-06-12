# -*- coding: utf-8 -*-

from openerp import models, fields, api, _, SUPERUSER_ID
from openerp.exceptions import UserError


class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    reserved_user_ids = fields.Many2many('res.users', string='Salseperson')

    @api.multi
    def block_property(self):
        for rec in self:
            if self.env.user.id != SUPERUSER_ID:
                if not self.env.user.has_group('sky_height.development_head_user') and not self.env.user.has_group('isky_access_rights.development_user'):
                    raise UserError('Only development team can make properties blocked')
            if rec.status == 'available':
                rec.status = 'blocked'
            else:
                raise UserError('Please Check Selected Lines, Only Properties in Available Status Can be Blocked')

    @api.multi
    def available_property(self):
        for rec in self:
            is_operation = self.env.user.has_group('sky_height.operation_sr_manager_user') or self.env.user.has_group('sky_height.operation_manager_user') or \
               self.env.user.has_group('sky_height.operation_senior_supervisor_user') or self.env.user.has_group('sky_height.operation_supervisor_user') or \
               self.env.user.has_group('sky_height.operation_sr_executive_user') or self.env.user.has_group('sky_height.operation_executive_user')
            is_development = self.env.user.has_group('sky_height.development_head_user') or self.env.user.has_group('isky_access_rights.development_user')
            is_sale_head = self.env.user.has_group('sky_height.sales_head_user')

            if is_development or is_operation or is_sale_head or self.env.user.id == SUPERUSER_ID:
                if is_development:
                    if rec.status == 'blocked':
                        rec.status = 'available'
                    else:
                        raise UserError(_('Please Check Selected Lines, Only Properties in Blocked Status Can be Available'))

                if is_sale_head or is_operation:
                    if rec.status == 'not_available':
                        rec.status = 'available'
                    else:
                        raise UserError(_('Please Check Selected Lines, Only Properties in Unavailable Status Can be Available'))
            else:
                raise UserError(_('Only development team or operation team or sale head can set properties to available'))
    @api.multi
    def update_state_to_available(self):
        for rec in self:
            is_development = self.env.user.has_group('sky_height.development_head_user') or self.env.user.has_group(
                'isky_access_rights.development_user')
            if self.env.user.has_group('base.group_sale_salesman') or self.env.user.has_group('sky_height.sales_head_user') or self.env.user.has_group('sky_height.sale_team_leader_group'):
                if rec.resp_user_id.id == self.env.user.id or self.env.user.id == SUPERUSER_ID or self.env.user.has_group('sky_height.sales_head_user'):
                    rec.resp_user_id = False
                    rec.write({'status': 'available'})
                else:
                    raise UserError(_("Only salesperson who set it to unavailable or operation department, can set it to available"))
            else:
                if is_development:
                    if rec.status != 'blocked':
                        raise UserError(_(
                            "You can only available blocked properties"))
                rec.write({'status': 'available','resp_user_id':False})

    @api.multi
    def write(self, vals):
        for rec in self:
            if self.env.user.id != SUPERUSER_ID:
                # Prevent Development head from editing property if it is in state (Reserved)
                if self.env.user.has_group('sky_height.development_head_user') or self.env.user.has_group('isky_access_rights.development_user'):
                        if rec.status == 'reserved':
                            raise UserError(_("You can't edit properties in (Reserved) state"))

                # Allow Operations security groups from editing only available properties
                if self.env.user.has_group('sky_height.operation_sr_manager_user') or self.env.user.has_group('sky_height.operation_manager_user') or \
                   self.env.user.has_group('sky_height.operation_senior_supervisor_user') or self.env.user.has_group('sky_height.operation_supervisor_user') or \
                   self.env.user.has_group('sky_height.operation_sr_executive_user') or self.env.user.has_group('sky_height.operation_executive_user'):
                    if rec.status not in ['available', 'not_available'] or not (vals.get('status') or 'resp_user_id' in vals.keys()):
                        raise UserError(_("You can only set properties to be (Available/Unavailable)"))

                # Prevent salesperson from edit property
                if self.env.user.has_group('base.group_sale_salesman') or self.env.user.has_group('sky_height.sale_team_leader_group') or self.env.user.has_group('base.group_sale_manager') or \
                        self.env.user.has_group('sky_height.sales_head_user'):
                    if not ('status' in vals.keys() or 'resp_user_id' in vals.keys() or 'reserved_user_ids' in vals.keys()):
                        raise UserError(_("You don't allow to edit properties"))

        return super(ProductProductInherit, self).write(vals)

    # Prevent development from delete properties if property is reserved
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.status in ['contracted', 'reserved', 'delivered']:
                raise UserError(_("You can't delete properites in that status (Delivery, Reserved, Contracted)"))
        return super(ProductProductInherit, self).unlink()


