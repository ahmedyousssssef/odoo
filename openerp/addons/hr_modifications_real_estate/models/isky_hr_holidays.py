from openerp.exceptions import UserError, AccessError
from openerp.osv import fields, osv
from openerp.tools.translate import _


class hr_holidays(osv.osv):
    _inherit = "hr.holidays"

    _columns = {
        'personal_charge': fields.many2one('hr.employee', string='Personal Charge'),
        'phone_during_vacation': fields.integer(string='Phone During Vacation'),
        'reason': fields.text(string='Reason'),
    }

    def holidays_first_validate(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids):
            if uid == rec.employee_id.parent_id.user_id.id:
                return self.write(cr, uid, ids,
                                  {'state': 'validate1','manager_id': rec.employee_id.parent_id.id},context=context)
            else:
                raise UserError(_("Only Employee's Manager can approve!"))
