# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
import datetime, time
from dateutil.relativedelta import relativedelta


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def _default_check_is_sales_head(self):
        if self.env.user.has_group('sky_height.sales_head_user'):
            return True
        else:
            return False

    is_sales_head = fields.Boolean(compute='_check_is_sales_head', default=_default_check_is_sales_head)

    def _check_is_sales_head(self):
        for rec in self:
            rec.is_sales_head = True if self.env.user.has_group('sky_height.sales_head_user') else False

    def _check_is_salesperson(self):
        for rec in self:
            rec.is_saleperson = True if self.env.user.has_group('base.group_sale_salesman') else False

    def get_domain(self):
        users = self.env['res.users'].search([])
        domain_users = []
        for user in users:
            if user.has_group('base.group_sale_salesman') or \
                    user.has_group('base.group_sale_salesman_all_leads') or \
                    user.has_group('base.group_sale_manager') or \
                    user.has_group('sky_height.sale_team_leader_group'):
                domain_users.append(user.id)
        return [('id', 'in', domain_users)]

    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user, domain=get_domain)
    name = fields.Char(string='Opportunity', required=False)
    project_id = fields.Many2one('project.project', _('Project'))
    phase_id = fields.Many2one('project.phase', _('Phase'))
    property_id = fields.Many2one('product.product', string='Property')
    marital_status = fields.Selection([('single', _("Single")), ('married', _("Married")), ('widowed', _("Widowed")),
                                       ('divorced', _("Divorced"))], _('Marital Status'))
    no_of_kids = fields.Integer(_('No. Of Family Member'))
    organization = fields.Char(_('Organization'))
    id_no = fields.Char(string="Identification No.")
    id_type = fields.Selection([('id', _("ID")), ('passport', _("Passport"))], string="Identification Type")
    id_photo = fields.Binary("Photo ID")
    user_ids = fields.Many2many('res.users', string='Sales Persons')
    broker_id = fields.Many2one('res.partner', string=_('Broker'), domain=[('is_broker', '=', True)])
    sales_type = fields.Selection([('direct', _("Direct")), ('indirect', _("Indirect")),
                                   ('individual_broker', _("Individual Broker")),
                                   ('client_referral', _("Client Referral")),
                                   ('employee_referral', _("Employee Referral")), ('resale', _("Resale")),
                                   ('upgrade', _("Upgrade")), ('supplier_through_sales', _("Supplier Through Sales")),
                                   ('supplier_through_company', _("Supplier Through Company"))], default='direct',
                                  string='Sales Type')

    source = fields.Selection([('facebook', _("Facebook")), ('callcenter', _("Call Center")), ('website', _("Website")),
                               ('broker', _("Broker")), ('referral', _("Referral")), ('ambassador', _("Ambassador")),
                               ('other', _("Other")), ('self_generated', _("Self Generated"))],
                              default='self_generated', string='Source')

    status = fields.Selection([('available', _('Available')), ('not_available', _('Not Available')),
                               ('reserved', _('Reserved')), ('contracted', _('Contracted')),
                               ('delivered', _('Delivered'))], string="Status", related='property_id.status')
    date_expiry = fields.Date(string="Expiry Date", compute='get_expiry_date', store=True)

    mobile1_type = fields.Selection([('local', 'Local'), ('foreign', 'Foreign')], string="Mobile1 Type")
    mobile2 = fields.Char('Mobile 2')
    mobile2_type = fields.Selection([('local', 'Local'), ('foreign', 'Foreign')], string="Mobile2 Type")
    note_ids = fields.One2many('lead.notes', 'lead_id')
    check_readonly = fields.Boolean(compute='check_sales_groups')
    note = fields.Text(string="Internal Notes (Feedback)", compute="get_expiry_date", store=True)
    source_id = fields.Many2one('utm.source', "Source", required=False)
    meetings_ids = fields.One2many('calendar.event', "opportunity_id")
    customer_id = fields.Many2one('res.partner', string="Customer")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    other = fields.Char("Other")

    @api.multi
    def name_get(self):
        res = super(CrmLead, self).name_get()
        for val in self:
            if val.type == 'lead':
                name = val.contact_name
                if val.source and name:
                    source = " - " + val.source
                    name = name + source
                    val.name = name
                    res.append((val.id, name))
        return res

    def check_sales_groups(self):
        if self.env.user.has_group('base.group_sale_salesman') or self.env.user.has_group('base.group_sale_manager')or self.env.user.has_group('sky_height.sale_team_leader_group'):
            self.check_readonly = True

    @api.onchange('mobile')
    def get_partner_from_mob(self):
        for val in self:
            if val.mobile:
                partner_obj = self.env['res.partner'].search([('mobile', '=', val.mobile)], limit=1)
                if partner_obj:
                    val.partner_id = partner_obj

    @api.onchange('mobile', 'mobile1_type')
    @api.constrains('mobile', 'mobile1_type')
    def validate_mobile_number(self):
        for val in self:
            if val.mobile and not val.mobile1_type:
                raise ValidationError(_("Sorry .. you must choose mobile 1 type !!"))

            if val.mobile:
                opp_obj = self.search(
                    ['&', '|', ('mobile', '=', val.mobile), ('mobile2', '=', val.mobile), ('active', '=', True)])

                partner_obj = self.env['res.partner'].search(
                    ['|', ('mobile', '=', val.mobile), ('mobile2', '=', val.mobile)])

                mobile = val.mobile

                if not (mobile.isdigit()):
                    raise ValidationError(_("Sorry .. mobile number must contain integers only !!"))

                if len(mobile) != 11 and val.mobile1_type == 'local':
                    raise ValidationError(_("Sorry .. mobile number must be 11 digit !!"))

                if len(mobile) < 11 and val.mobile1_type == 'foreign':
                    raise ValidationError(_("Sorry .. mobile number must be at least 11 digit !!"))

                if len(opp_obj) > 1:
                    raise ValidationError(_("Sorry .. this mobile number is already exist !!"))
                if partner_obj:
                    raise ValidationError(_("This mobile is already exist with customer %s") % partner_obj[0].name)

    @api.onchange('mobile2', 'mobile2_type')
    @api.constrains('mobile2', 'mobile2_type')
    def validate_mobile2_number(self):
        for val in self:
            if val.mobile2 and not val.mobile2_type:
                raise ValidationError(_("Sorry .. you must choose mobile 2 type !!"))

            if val.mobile2:
                opp_obj = self.search(
                    ['&', '|', ('mobile', '=', val.mobile2), ('mobile2', '=', val.mobile2), ('active', '=', True)])
                partner_obj = self.env['res.partner'].search(
                    ['|', ('mobile', '=', val.mobile2), ('mobile2', '=', val.mobile2)])
                mobile = val.mobile2

                if not (mobile.isdigit()):
                    raise ValidationError(_("Sorry .. mobile number must contain integers only !!"))

                if len(mobile) != 11 and val.mobile2_type == 'local':
                    raise ValidationError(_("Sorry .. mobile number must be 11 digit !!"))

                if len(mobile) < 11 and val.mobile2_type == 'foreign':
                    raise ValidationError(_("Sorry .. mobile number must be at least 11 digit !!"))

                if len(opp_obj) > 1:
                    raise ValidationError(_("Sorry .. this mobile number is already exist !!"))

                if partner_obj:
                    raise ValidationError(_("This mobile is already exist with customer %s") % partner_obj[0].name)

    @api.depends('note_ids', 'create_date')
    def get_expiry_date(self):
        for rec in self:
            lead_period = self.env['ir.values'].get_default('sale.config.settings', 'lead_period')
            if not lead_period:
                lead_period = 0
            last_note = self.env['lead.notes'].search([('lead_id', '=', rec.id)], limit=1, order='id DESC')

            if last_note:
                rec.note = last_note.note
                date = fields.Date.from_string(last_note.create_date)
                expiry_date = (date + relativedelta(days=lead_period))
                rec.date_expiry = expiry_date

            if not rec.note_ids:
                if lead_period and rec.create_date:
                    rec.date_expiry = (datetime.datetime.strptime(rec.create_date, "%Y-%m-%d %H:%M:%S")).date() + \
                                      datetime.timedelta(days=lead_period)

    @api.multi
    @api.constrains('contact_name', 'email_from')
    def _check_customer(self):
        for rec in self:
            if rec.contact_name or rec.email_from:
                search_objs = self.search([('contact_name', '=', rec.contact_name),
                                           ('email_from', '=', rec.email_from)])
                if len(search_objs) > 1:
                    raise ValidationError(_('There is already Lead with the same data'))

    @api.multi
    @api.onchange('project_id')
    def on_change_project(self):
        for rec in self:
            rec.phase_id = False
            rec.unit_ids = False
            all_phases = []
            phases = self.env['project.phase'].search(
                [('project_id', '=', rec.project_id.id), ('available', '=', True)])
            for phase in phases:
                all_phases.append(phase.id)
            return {'domain': {'phase_id': [('id', 'in', all_phases)]}}

    @api.multi
    @api.onchange('phase_id')
    def on_change_phase(self):
        for rec in self:
            all_properties = []
            properties = self.env['product.product'].search([('project_id', '=', rec.project_id.id),
                                                             ('phase_id', '=', rec.phase_id.id),
                                                             ('type', '=', 'property'),
                                                             ('status', '=', 'available')])
            for property in properties:
                all_properties.append(property.id)
            return {'domain': {'property_id': [('id', 'in', all_properties)]}}

    @api.multi
    def create_reservation(self):
        vals = {}
        new_customer = 0
        for rec in self:
            if not rec.source:
                raise ValidationError(_("Please Add Source"))
            elif not rec.mobile:
                raise ValidationError(_("Please Add Mobile1 Number"))
            elif not rec.date_expiry:
                raise ValidationError(_("Please Add Expiry Date"))
            elif not rec.contact_name:
                raise ValidationError(_("Please Add Contact Name"))
            elif not rec.street:
                raise ValidationError(_("Please Add Street"))
            elif not rec.sales_type:
                raise ValidationError(_("Please Add Sales Type"))
            elif not rec.function:
                raise ValidationError(_("Please Add Job Title"))

            elif not rec.partner_id:
                if rec.partner_name or rec.contact_name:
                    vals.update({'name': rec.partner_name or rec.contact_name,
                                 'street': rec.street,
                                 'street2': rec.street2,
                                 'country_id': rec.country_id.id,
                                 'mobile1_type': rec.mobile1_type,
                                 'mobile': rec.mobile,
                                 'mobile2_type': rec.mobile2_type,
                                 'mobile2': rec.mobile2,
                                 'fax': rec.fax,
                                 'city': rec.city,
                                 'state_id': rec.state_id.id,
                                 'zip': rec.zip,
                                 'opt_out': rec.opt_out,
                                 'customer': True,
                                 'type': 'contact',
                                 'organization': rec.organization,
                                 'function': rec.function,
                                 'email': rec.email_from,
                                 'other': rec.other,
                                 'user_id': self.env.user.id
                                 })
                new_customer_object = self.env['res.partner'].with_context(force_create_customer=True).create(vals)

                new_customer = new_customer_object.id
                rec.partner_id = new_customer

            # users = [user.id for user in rec.user_ids]
            # broker_ids = [broker.id for broker in rec.broker_ids]

            res = self.env['ir.model.data'].get_object_reference('sky_height', 'rsreservation_form_view')
            view_id = res and res[1] or False

            ctx = {
                'default_project_id': rec.project_id.id,
                'default_phase_id': rec.phase_id.id,
                'default_customer_id': rec.partner_id.id or False,
                'default_user_ids': [(4, rec.user_id.id)] if rec.user_id else False,
                'default_broker_ids': [(4, rec.broker_id.id)] if rec.broker_id else False,
                'default_sales_team_id': rec.team_id.id,
                'default_sales_type': rec.sales_type,
                'default_lead_id': rec.id,
                'default_marital_status': rec.marital_status,
                'default_no_of_kids': rec.no_of_kids,
                'default_function': rec.function,
                'default_id_no': rec.id_no or False,
                'default_id_type': rec.id_type or False,
                'default_id_photo': rec.id_photo or False,
                'default_sales_customer_id': rec.customer_id.id or False,
                'default_sales_employee_id': rec.employee_id.id or False,
                'default_other': rec.other,
                'default_source': rec.source,
            }

            return {
                'name': _("Create Reservation"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'rs.reservation',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'context': ctx,
            }


class LeadNotes(models.Model):
    _name = "lead.notes"
    _order = 'create_date desc'

    note = fields.Text('Note', required=True)
    lead_id = fields.Many2one('crm.lead', ondelete="cascade")
