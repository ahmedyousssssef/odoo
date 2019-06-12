from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    use_prepayment_account = fields.Boolean('Use Prepayment account',
                                            help="Check this if you want to input a prepayment on the prepayment accounts.")
    use_unearned_revenu_account = fields.Boolean('Use Unearned Revenu account',
                                                 help="Check this if you want to input a unearned revenu on the prepayment accounts.")
    use_extension_account = fields.Boolean('Use Extension account',
                                           help="Check this if you want to input Extension on the prepayment accounts.")

    @api.one
    @api.constrains('use_prepayment_account', 'use_extension_account', 'use_unearned_revenu_account')
    def _check_fields(self):
        if self.use_prepayment_account and self.use_extension_account:
            raise ValidationError(
                _('You Can not select Use Prepayment account and Use Extension account in the same payment'))
        if self.use_prepayment_account and self.use_unearned_revenu_account:
            raise ValidationError(
                _('You Can not select Use Prepayment account and Use Unearned account in the same payment'))
        if self.use_extension_account and self.use_unearned_revenu_account:
            raise ValidationError(
                _('You Can not select Use Extension account and Use Unearned account in the same payment'))

    @api.one
    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        if self.invoice_ids:
            self.destination_account_id = self.invoice_ids[0].account_id.id
        elif self.payment_type == 'transfer':
            if not self.company_id.transfer_account_id.id:
                raise UserError(_('Transfer account not defined on the company.'))
            self.destination_account_id = self.company_id.transfer_account_id.id

        elif self.partner_id:
            if self.partner_type == 'customer':
                if self.use_extension_account:
                    if not self.partner_id.extension_account_prereceivable.id:
                        raise UserError(_('Please configure the partner Extension Prereceivable Account at first!'))
                    else:
                        self.destination_account_id = self.partner_id.extension_account_prereceivable.id
                if self.use_prepayment_account:
                    if not self.partner_id.property_account_prereceivable.id:
                        raise UserError(_('Please configure the partner Prereceivable Account at first!'))
                    else:
                        self.destination_account_id = self.partner_id.property_account_prereceivable.id
                if self.use_unearned_revenu_account:
                    if not self.partner_id.property_unearned_revenu_account_prereceivable.id:
                        raise UserError(_('Please configure the partner Unearned revenu Account at first!'))
                    else:
                        self.destination_account_id = self.partner_id.property_unearned_revenu_account_prereceivable.id

                if not self.use_prepayment_account and not self.use_extension_account \
                        and not self.use_unearned_revenu_account:
                    self.destination_account_id = self.partner_id.property_account_receivable_id.id
            else:

                if not self.use_prepayment_account:
                    self.destination_account_id = self.partner_id.property_account_payable_id.id
