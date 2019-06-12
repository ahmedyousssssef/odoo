
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ProjectConfigSettings(models.TransientModel):
    _inherit = 'project.config.settings'
    _name = 'project.config.settings'

    achievement_share = fields.Float(string='Achievement Share')
    quality_share = fields.Float(string='Quality Share')


    @api.multi
    def set_achievement_share(self):
        values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            if config.achievement_share < 0 or config.achievement_share > 100:
                raise ValidationError(_("Percentage must be between 0 and 100%"))
            values.set_default('project.config.settings', 'achievement_share',
                               config.achievement_share)

    @api.multi
    def set_quality_share(self):
        values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            if config.quality_share < 0 or config.quality_share > 100:
                raise ValidationError(_("Percentage must be between 0 and 100%"))
            values.set_default('project.config.settings', 'quality_share',
                               config.quality_share)

