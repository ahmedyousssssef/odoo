# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class HrAppraisalSettings(models.TransientModel):
    _name = 'hr.appraisal.settings'
    _inherit = 'res.config.settings'

    technical_share = fields.Float(string='Technical Share')
    timeline_share = fields.Float(string='Timeline Share')
    net_technical = fields.Float(string='Net Technical')
    competencies_evaluation = fields.Float(string='Competencies Evaluation')



    @api.multi
    def set_technical_share(self):
        values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            if config.technical_share < 0 or config.technical_share > 100:
                raise ValidationError(_("Percentage must be between 0 and 100%"))
            values.set_default('hr.appraisal.settings', 'technical_share',
                               config.technical_share)

    @api.multi
    def set_timeline_share(self):
        values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            if config.timeline_share < 0 or config.timeline_share > 100:
                raise ValidationError(_("Percentage must be between 0 and 100%"))
            values.set_default('hr.appraisal.settings', 'timeline_share',
                               config.timeline_share)


    @api.multi
    def set_net_technical(self):
        values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            if config.net_technical < 0 or config.net_technical > 100:
                raise ValidationError(_("Percentage must be between 0 and 100%"))
            values.set_default('hr.appraisal.settings', 'net_technical',
                               config.net_technical)

    @api.multi
    def set_competencies_evaluation(self):
        values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            if config.competencies_evaluation < 0 or config.competencies_evaluation > 100:
                raise ValidationError(_("Percentage must be between 0 and 100%"))
            values.set_default('hr.appraisal.settings', 'competencies_evaluation',
                               config.competencies_evaluation)

