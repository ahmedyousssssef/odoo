from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ChangePropertyStatus(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    def get_domain(self):
        users = self.env['res.users'].search([])
        domain_users = []
        for user in users:
            if user.has_group('sky_height.sale_team_leader_group') or user.has_group('base.group_sale_salesman'):
                domain_users.append(user.id)
        return [('id', 'in', domain_users)]

    @api.onchange('user_id')
    def get_team(self):
        teams = self.env['crm.team'].search([])
        domain_team = []
        for team in teams:
            for user in self.user_id:
                if user in team.member_ids:
                    self.team_id = team.id
                    domain_team.append(team.id)

    action = fields.Selection([('nothing', 'Do not link to a customer')], 'Related Customer', required=True,
                              default='nothing')

    name = fields.Selection(string="Conversion Action", selection=[('convert', 'Convert to Lead')], required=True, )

    user_id = fields.Many2one('res.users', string='Salesperson', domain=get_domain)

    def action_apply(self, cr, uid, ids, context=None):
        res = super(ChangePropertyStatus, self).action_apply(cr, uid, ids, context)
        obj = self.pool.get('crm.lead').browse(cr, uid, res['res_id'])
        obj.check_readonly = True
        return res

    @api.constrains('user_id')
    def check_salesperson(self):
        for val in self:
            if not (val.user_id.has_group('base.group_sale_salesman') or \
                    val.user_id.has_group('base.group_sale_salesman_all_leads') or \
                    val.user_id.has_group('base.group_sale_manager') or \
                    val.user_id.has_group('sky_height.sale_team_leader_group')):
                raise ValidationError("Please Insert valid salesperson!!")
