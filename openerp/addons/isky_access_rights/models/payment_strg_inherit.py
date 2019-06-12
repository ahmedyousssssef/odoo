# -*- coding: utf-8 -*-

from openerp import models, api, _
from openerp.exceptions import ValidationError


class PaymentStrgInherit(models.Model):
    _inherit = 'payment.strg'

    # Override for prevent treasury from editing payment term (Only click on buttons)
    # @api.multi
    # def write(self, vals):
    #     if self.env.user.has_group("isky_access_rights.group_treasury"):
    #         if not (len(set(['status', 'penalty_fees', 'deduction_amount', 'apply_penalty', 'penalty_date', 'penalty_journal_id', 'penalty_journal_entry_id', 'collected_journal_entry_id', 'cheque_status', 'rejection_action']).intersection(set(vals.keys()))) != 0):
    #             raise ValidationError(_("You can't edit payment details"))
    #     return super(PaymentStrgInherit, self).write(vals)
