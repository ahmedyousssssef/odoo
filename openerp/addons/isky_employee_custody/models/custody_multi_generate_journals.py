# -*- coding: utf-8 -*-
from openerp import models, api, _
from openerp.exceptions import UserError


class CustodyMultiGenerateJournals(models.TransientModel):
    _name = "custody.multi.generate.journals"
    _description = "Generate Journals for Selected Journals"

    @api.multi
    def generate_journals(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['employee.custody'].browse(active_ids):
            if record.state not in ('draft', 'open'):
                raise UserError(
                    _("Selected custody(s) cannot be confirmed as they are not in 'new' or 'open' state."))
            record.with_context({'button_type': 'receive'}).button_journal_entry()

        return {'type': 'ir.actions.client', 'tag': 'reload'}
