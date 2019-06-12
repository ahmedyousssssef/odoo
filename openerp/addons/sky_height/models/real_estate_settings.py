# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class SkyHeightConfigSettings(models.TransientModel):
    _name = 'sky.height.settings'
    _inherit = 'res.config.settings'

    penalty_percentage = fields.Float(string='Penalty Percentage')
    penalty_revenue_account_id = fields.Many2one('account.account', string='Penalty Fees Account')
    reservation_journal_id = fields.Many2one('account.journal', string='Reservation Journal')
    maintaince_journal_id = fields.Many2one('account.journal', string='Maintaince Journal')
    under_collection_journal_id = fields.Many2one('account.journal', string='Under Collection Journal')
    reservation_expiry = fields.Integer(string='Reservation Expiry Days', default=30)
    commission_journal_id = fields.Many2one('account.journal', string="Commission Journal")
    reject_journal_id = fields.Many2one('account.journal', string="Rejection Journal")

    @api.multi
    def set_commission_journal_id(self):
        values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            values.set_default('sky.height.settings', 'commission_journal_id',
                               config.commission_journal_id.id)


    @api.multi
    def set_reject_journal_id(self):
        values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            values.set_default('sky.height.settings', 'reject_journal_id',
                               config.reject_journal_id.id)



    @api.multi
    def set_penalty_percentage(self):
        values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            if config.penalty_percentage < 0 or config.penalty_percentage > 100:
                raise ValidationError(_("Percentage must be between 0 and 100%"))
            values.set_default('sky.height.settings', 'penalty_percentage',
                               config.penalty_percentage)

    @api.multi
    def set_penalty_revenue_account_id(self):
        values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            values.set_default('sky.height.settings', 'penalty_revenue_account_id',
                               config.penalty_revenue_account_id.id)


    @api.multi
    def set_reservation_journal_id(self):
        values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            values.set_default('sky.height.settings', 'reservation_journal_id',
                               config.reservation_journal_id.id)
    @api.multi
    def set_under_collection_journal_id(self):
        values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            values.set_default('sky.height.settings', 'under_collection_journal_id',
                               config.under_collection_journal_id.id)


    @api.multi
    def set_maintaince_journal_id(self):
        values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            values.set_default('sky.height.settings', 'maintaince_journal_id',
                               config.maintaince_journal_id.id)


    @api.multi
    def set_default_reservation_expiry(self):
        values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            values.set_default('sky.height.settings', 'reservation_expiry', config.reservation_expiry)
