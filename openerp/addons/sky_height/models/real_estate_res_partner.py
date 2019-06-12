# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_broker = fields.Boolean(_('Broker'))
    broker_commission_amount = fields.Float(_('Broker Commission Percentage'))
    broker_commission_account = fields.Many2one('account.account', _('Broker Commission Account'))
    organization = fields.Char(_('Organization'))
    partner_code = fields.Char(string="Partner Code", readonly=True, copy=False)
    mobile1_type = fields.Selection([('local', 'Local'), ('foreign', 'Foreign')], string="Mobile1 Type")
    mobile2 = fields.Char('Mobile 2')
    mobile2_type = fields.Selection([('local', 'Local'), ('foreign', 'Foreign')], string="Mobile2 Type")

    @api.model
    def create(self, values):
        values['partner_code'] = self.env['ir.sequence'].next_by_code('real.estate.customer.code.seq')
        return super(ResPartner, self).create(values)

    @api.multi
    @api.constrains('broker_commission_amount')
    def _check_commission_amount(self):
        for obj in self:
            if obj.broker_commission_amount:
                if obj.broker_commission_amount <= 0:
                    raise ValidationError(_('Commission Amount Must be Greater Than Zero'))
                if obj.broker_commission_amount >= 100:
                    raise ValidationError(_('Commission Amount Must Be < 100'))

    @api.onchange('mobile', 'mobile1_type')
    @api.constrains('mobile', 'mobile1_type')
    def check_mobile1_no(self):
        for val in self:
            if val.mobile and not val.mobile1_type:
                raise ValidationError(_("Sorry .. you must choose mobile 1 type !!"))
            if val.mobile:
                mobile = val.mobile
                partner_obj = self.search(['|',('mobile', '=', val.mobile), ('mobile2', '=', val.mobile)]).ids
                lead_obj = self.env['crm.lead'].search(
                    ['&','|',('mobile', '=', val.mobile), ('mobile2', '=', val.mobile),'&', ('active', '=', True), ('partner_id', '=', False)])

                if len(mobile) != 11 and val.mobile1_type == 'local':
                    raise ValidationError(_("Sorry .. mobile number must be 11 digit !!"))

                if len(mobile) < 11 and val.mobile1_type == 'foreign':
                    raise ValidationError(_("Sorry .. mobile number must be at least 11 digit !!"))

                if not (mobile.isdigit()):
                    raise ValidationError(_("Sorry .. Mobile number must contain integers only !!"))

                if len(partner_obj) > 1:
                    if val.id in partner_obj:
                        partner_obj.remove(val.id)
                    raise ValidationError(
                        _('Mobile Number Already exist with customer (%s)') % self.search([('id', 'in', partner_obj)],
                                                                                          limit=1).name)

                if lead_obj:
                    ctx = self._context
                    if 'force_create_customer' in ctx:
                        if not ctx['force_create_customer']:
                            raise ValidationError(_("Sorry .. This mobile is already exist with active lead"))
                    else:
                        raise ValidationError(_("Sorry .. This mobile is already exist with active lead"))

    @api.onchange('mobile2', 'mobile2_type')
    @api.constrains('mobile2', 'mobile2_type')
    def check_mobile2_no(self):
        for val in self:
            if val.mobile2 and not val.mobile2_type:
                raise ValidationError(_("Sorry .. you must choose mobile 2 type !!"))
            if val.mobile2:
                mobile = val.mobile2
                partner_obj = self.search(['|', ('mobile', '=', val.mobile2), ('mobile2', '=', val.mobile2)]).ids
                lead_obj = self.env['crm.lead'].search(
                    ['&','|', ('mobile', '=', val.mobile2), ('mobile2', '=', val.mobile2),'&', ('active', '=', True),
                     ('partner_id', '=', False)])

                if len(mobile) != 11 and val.mobile2_type == 'local':
                    raise ValidationError(_("Sorry .. mobile number must be 11 digit !!"))

                if len(mobile) < 11 and val.mobile2_type == 'foreign':
                    raise ValidationError(_("Sorry .. mobile number must be at least 11 digit !!"))

                if not (mobile.isdigit()):
                    raise ValidationError(_("Sorry .. Mobile number must contain integers only !!"))

                if len(partner_obj) > 1:
                    if val.id in partner_obj:
                        partner_obj.remove(val.id)
                    raise ValidationError(
                        _('Mobile Number Already exist with customer (%s)') % self.search([('id', 'in', partner_obj)],
                                                                                          limit=1).name)

                if lead_obj:
                    ctx = self._context
                    if 'force_create_customer' in ctx:
                        if not ctx['force_create_customer']:
                            raise ValidationError(_("Sorry .. This mobile is already exist with active lead"))
                    else:
                        raise ValidationError(_("Sorry .. This mobile is already exist with active lead"))