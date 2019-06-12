# -*- coding: utf-8 -*-


from openerp import models, fields, api, _

class ProjectProject(models.Model):
    _inherit='project.project'

    phase_ids = fields.One2many('project.phase', 'project_id', _('Phases'))
    terms_conditions = fields.Html("Terms and Conditions")


class ProjectPhase(models.Model):
    _name='project.phase'

    name = fields.Char('Name')


    phase_no = fields.Integer('Phase NO.')
    available = fields.Boolean('Available',default=True)
    project_id = fields.Many2one('project.project', _('Project'),domain=[('is_kpi', '=', False)])
    property_line_ids = fields.One2many('project.property', 'phase_id', _('Properties'))

    @api.multi
    def get_property(self):
        for rec in self:
            rec.property_line_ids = {}
            property_pool = self.env['product.product']
            prop_objects = property_pool.search([('phase_id', '=', rec.id),
                                                 ('project_id', '=', rec.project_id.id)])

            if prop_objects:
                for prop in prop_objects:

                    self.env['project.property'].create({'phase_id': rec.id,
                                                        'project_id': prop.project_id.id,
                                                        'property_id': prop.id,
                                                        'property_block_id': prop.property_block_id.id,
                                                        'property_no': prop.property_no,
                                                        'lst_price': prop.lst_price,
                                                        'type_of_property_id': prop.type_of_property_id.id,
                                                        'level_id': prop.level_id.id,
                                                        'total_area': prop.total_area})


    @api.multi
    def update_properties_state_to_available(self):
        property_pool = self.env['product.product']
        for rec in self:
            prop_objects = property_pool.search([('phase_id', '=', rec.id),
                                                 ('project_id', '=', rec.project_id.id),
                                                 ('status','in',['available','not_available'])])

            if prop_objects:
                for prop in prop_objects:
                    prop.write({'status': 'available'})

    @api.multi
    def update_properties_state_to_not_available(self):
        property_pool = self.env['product.product']
        for rec in self:
            prop_objects = property_pool.search([('phase_id', '=', rec.id),
                                                 ('project_id', '=',rec.project_id.id),
                                                 ('status','in',['available','not_available'])])

            if prop_objects:
                for prop in prop_objects:
                    prop.write({'status': 'not_available'})

class ProjectProperty(models.Model):
    _name = "project.property"

    project_id = fields.Many2one('project.project', _('Project'),domain=[('is_kpi', '=', False)])
    phase_id = fields.Many2one('project.phase', _('Phase'))
    property_id = fields.Many2one('product.product', _('Property'))
    property_no = fields.Integer(string="Property Number")
    property_block_id = fields.Many2one('property.block', _('Block'))
    type_of_property_id = fields.Many2one('property.type', _('Type'))
    level_id = fields.Many2one('property.level', _('Level'))
    total_area = fields.Float(_('Total Area'))



