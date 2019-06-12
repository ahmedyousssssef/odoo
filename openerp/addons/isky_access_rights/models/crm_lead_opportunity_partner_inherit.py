# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp import models, api, _, SUPERUSER_ID
from openerp.exceptions import UserError

class CrmLead2OpportunityPartner(osv.osv_memory):
    _inherit = 'crm.lead2opportunity.partner'

    # Prevent operations security groups from view lead after click on (Convert to lead) button
    def action_apply(self, cr, uid, ids, context=None):
        """
        Convert lead to opportunity or merge lead and opportunity and open
        the freshly created opportunity view.
        """
        if context is None:
            context = {}

        lead_obj = self.pool['crm.lead']
        partner_obj = self.pool['res.partner']

        w = self.browse(cr, uid, ids, context=context)[0]
        opp_ids = [o.id for o in w.opportunity_ids]
        vals = {
            'team_id': w.team_id.id,
        }
        if w.partner_id:
            vals['partner_id'] = w.partner_id.id
        if w.name == 'merge':
            lead_id = lead_obj.merge_opportunity(cr, uid, opp_ids, context=context)
            lead_ids = [lead_id]
            lead = lead_obj.read(cr, uid, lead_id, ['type', 'user_id'], context=context)
            if lead['type'] == "lead":
                context = dict(context, active_ids=lead_ids)
                vals.update({'lead_ids': lead_ids, 'user_ids': [w.user_id.id]})
                self._convert_opportunity(cr, uid, ids, vals, context=context)
            elif not context.get('no_force_assignation') or not lead['user_id']:
                vals.update({'user_id': w.user_id.id})
                lead_obj.write(cr, uid, lead_id, vals, context=context)
        else:
            lead_ids = context.get('active_ids', [])
            vals.update({'lead_ids': lead_ids, 'user_ids': [w.user_id.id]})
            self._convert_opportunity(cr, uid, ids, vals, context=context)
        if not (self.pool.get('res.users').has_group(cr, uid, 'sky_height.operation_sr_manager_user') or self.pool.get('res.users').has_group(cr, uid, 'sky_height.operation_manager_user') or \
            self.pool.get('res.users').has_group(cr, uid, 'sky_height.operation_senior_supervisor_user') or  self.pool.get('res.users').has_group(cr, uid, 'sky_height.operation_supervisor_user') or \
            self.pool.get('res.users').has_group(cr, uid, 'sky_height.operation_sr_executive_user') or self.pool.get('res.users').has_group(cr, uid, 'sky_height.operation_executive_user')):

            return self.pool.get('crm.lead').redirect_opportunity_view(cr, uid, lead_ids[0], context=context)
        else:
            menuitem_id = self.pool.get('ir.ui.menu').search(cr, uid, [('name', '=', 'Welcome Card')])

            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {'menu_id': menuitem_id[0] if menuitem_id else False}
            }

class CrmLeadInherit(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def create(self, vals):
        print(SUPERUSER_ID)
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('sky_height.sales_head_user'):
                raise UserError(_("You can't create lead"))
        return super(CrmLeadInherit, self).create(vals)
