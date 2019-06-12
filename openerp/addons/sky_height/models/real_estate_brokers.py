# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class PropertyBroker(models.Model):
    _name = 'property.broker'

    broker_id = fields.Many2one('res.partner', _('Broker'), domain=[('is_broker', '=', True)])
    commission_amount = fields.Float(_('Commission Percentage'))

    @api.constrains('commission_amount')
    def _check_commission_amount(self):
        for obj in self:
            if obj.commission_amount:
                if obj.commission_amount <= 0:
                    raise ValidationError(_('Commission Amount Must be Greater than Zero'))
                if obj.commission_amount >=100:
                    raise ValidationError(_('Commission Amount Must be < 100'))