# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError,UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _get_product_template_type(self):
        res = super(ProductTemplate, self)._get_product_template_type()
        if 'property' not in [item[0] for item in res]:
            res.append(('property', _('Property')))
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'
    _description = 'Real estate property'


    @api.multi
    def available_property(self):
        for rec in self:
            if rec.status == 'blocked':
                rec.status = 'available'
            else:
                raise UserError('Please Check Selected Lines, Only Properties in Blocked Status Can be Available')

    @api.multi
    @api.depends('project_id')
    def get_phase(self):
        for rec in self:
            all_phases = []
            phases = self.env['project.phase'].search(
                [('project_id', '=', rec.project_id.id), ('available', '=', True)])
            for phase in phases:
                all_phases.append(phase.id)
            if all_phases:
                phase_obj = self.env['project.phase'].browse(all_phases[0])
                rec.phase_id = phase_obj.id

    payment_id = fields.Many2one('account.payment', string='Payment')
    property_no = fields.Integer(string="Property Number", copy=False)
    project_id = fields.Many2one('project.project', _('Project'), domain=[('is_kpi', '=', False)])
    phase_id = fields.Many2one('project.phase', _('Phase'), compute=get_phase, store=True)
    search_admin = fields.Boolean(string="Admin", compute='_search_admin')
    status = fields.Selection([('blocked', _('Blocked')),('available', _('Available')), ('not_available', _('Not Available')),
                               ('reserved', _('Reserved')), ('contracted', _('Contracted')),
                               ('delivered', _('Delivered'))], string="Status", default='available', copy=False)

    property_block_id = fields.Many2one('property.block', _('Block'))
    type_of_property_id = fields.Many2one('property.type', _('Property Type'))

    level_id = fields.Many2one('property.level', _('Level'))
    total_area = fields.Float(_('Total Area'))
    total_open_area = fields.Float(_('Total Open Area'))

    property_floor_id = fields.Many2one('property.floor', _('Floor Number'))
    property_platform_id = fields.Many2one('property.platform', _('Property Platform'))
    bedrooms_no = fields.Integer(_('Bedrooms No.'))

    plot_area = fields.Float(_('Plot Area'))
    indoor_area = fields.Float(_('Indoor Area'))
    covered_terrace = fields.Float(_('Covered Terrace'))
    total_covered_area = fields.Float(_('Total Covered Area'))
    open_terrace = fields.Float(_('Open Terrace'))
    court_yard = fields.Float(_('Court Yard'))

    garden = fields.Boolean(string="Garden")
    garden_area = fields.Float(string="Garden Area")
    property_pool = fields.Boolean(string='Pool')
    pool_dimensions = fields.Char(string="Pool Dimensions")
    pool_area = fields.Float(string="Pool Area")

    corner = fields.Boolean(string="Corner")
    garage = fields.Boolean(string="Garage")
    sea_view = fields.Boolean(string="Sea View")
    clear_view = fields.Boolean(string="Clear View")
    lake_or_pool_view = fields.Boolean(string="Lake/Pool View")
    landscape_view = fields.Boolean(string="Landscape View")
    main_spine = fields.Boolean(string="Main Spine")
    resp_user_id = fields.Many2one('res.users', string='Responsible User', readonly=True)


    @api.multi
    @api.depends('status')
    def _search_admin(self):
        user = self.env['res.users'].browse(self.env.uid)
        for rec in self:
            rec.search_admin = True if not user.has_group(
                'sky_height.group_sky_height_admin') and rec.status != 'available' else False

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
    def update_state_to_available(self):
        for rec in self:
            rec.sudo().write({'status': 'available','resp_user_id':False})

    @api.multi
    def update_state_to_blocked(self):
        for rec in self:
            rec.write({'status': 'blocked'})

    @api.multi
    def update_state_to_not_available(self):
        for rec in self:
            rec.sudo().write({'status': 'not_available'})

    @api.constrains('total_area')
    def _check_total_area(self):
        for obj in self:
            if obj.type == 'property':
                if obj.total_area <= 0:
                    raise ValidationError(_('Total Area Must be greater Than Zero'))

    @api.constrains('property_no')
    def _check_property_no(self):
        property_ids = self.search([('property_no', '=', self.property_no)])
        if len(property_ids) > 1 and self.type == 'property':
            raise ValidationError(_('Property Number already exist!'))

    @api.multi
    def create_reservation(self):
        res = self.env['ir.model.data'].get_object_reference('sky_height', 'rsreservation_form_view')
        view_id = res and res[1] or False

        ctx = {
            'default_project_id': self.project_id.id,
            'default_phase_id': self.phase_id.id,
            'default_unit_ids': [(6, 0, [self.id])],
            'default_source': 'self_generated',
            'default_sales_type': 'direct'
        }
        return {
            'name': _("Create Reservation"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'rs.reservation',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': ctx,
        }


class PropertyLevel(models.Model):
    _name = "property.level"
    _description = "Property Level"

    name = fields.Char('Property Level', required=True, translate=True)


class PropertyType(models.Model):
    _name = "property.type"
    _description = "Property Types"

    name = fields.Char('Property Type', required=True, translate=True)


class PropertyPlatform(models.Model):
    _name = "property.platform"
    _description = "Property Platform"

    name = fields.Char('Platform', required=True, translate=True)


class PropertyFloor(models.Model):
    _name = "property.floor"
    _description = "Property Floor"

    name = fields.Char('Floor', required=True, translate=True)


class PropertyBlock(models.Model):
    _name = "property.block"
    _description = "Property Block"

    name = fields.Char(_('Block'), required=True)
