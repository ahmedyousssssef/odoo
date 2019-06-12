# -*- coding: utf-8 -*-

import time
import datetime
from openerp.osv import osv
from openerp.report import report_sxw


class report_rsreservation(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(report_rsreservation, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'compute_date_and_amount': self._compute_date_and_amount,
        })
        self.context=context

    def _compute_date_and_amount(self,date , days):
        if days ==0:

            date_order = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            result = date_order+datetime.timedelta(days)
        else:
            result= date
        return result


class report_report_rsreservation(osv.AbstractModel):
    _name = 'report.real_estate_new.report_property_reservation_document'
    _inherit = 'report.abstract_report'
    _template = 'real_estate_new.report_property_reservation_document'
    _wrapped_report_class = report_rsreservation
