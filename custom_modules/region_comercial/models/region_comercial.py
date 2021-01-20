# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class partner_region_comercial(models.Model):

    _inherit = 'res.partner'

    x_region_comercial = fields.Selection(selection=[
            ('andalucia_este', 'Andalucía Este'),
            ('andorra', 'Andorra'),
            ('aragon', 'Aragón'),
            ('asturias_cantabria', 'Asturias y Cantabria'),
            ('balears', 'Balears'),
            ('canarias', 'Canarias'),
            ('castilla leon', 'Castilla León'),
            ('castilla la mancha', 'Castilla la Mancha'),
            ('catalunya', 'Catalunya'),
            ('extremadura', 'Extremadura'),
            ('madrid', 'Madrid'),
            ('navarra', 'Navarra y la Rioja'),
            ('pais_vasco', 'País Vasco'),
        ], string='Región comercial')


    def write(self, vals):
        super(partner_region_comercial, self).write(vals)
        for partner in self:
            if vals.get('x_region_comercial', False):
                crm_leads = self.env['crm.lead'].search([('partner_id','=',partner.id)])
                if crm_leads:
                    crm_leads.write({
                        'x_partner_region_comercial': vals['x_region_comercial']
                    })


class crm_group_region_comercial(models.Model):

    _inherit = 'crm.lead'

    x_partner_region_comercial = fields.Selection(selection=[
            ('andalucia_este', 'Andalucía Este'),
            ('andorra', 'Andorra'),
            ('aragon', 'Aragón'),
            ('asturias_cantabria', 'Asturias y Cantabria'),
            ('balears', 'Balears'),
            ('canarias', 'Canarias'),
            ('castilla leon', 'Castilla León'),
            ('castilla la mancha', 'Castilla la Mancha'),
            ('catalunya', 'Catalunya'),
            ('extremadura', 'Extremadura'),
            ('madrid', 'Madrid'),
            ('navarra', 'Navarra y la Rioja'),
            ('pais_vasco', 'País Vasco'),
        ], string="Región Comercial")

    @api.model
    def create(self, vals):
        if vals.get('partner_id', False):
            partner = self.env['res.partner'].search([('id','=',vals['partner_id'])])
            vals['x_partner_region_comercial'] = partner.x_region_comercial
        return super(crm_group_region_comercial, self).create(vals)

class ActivityReport(models.Model):

    _inherit = "crm.activity.report"

    x_region_comercial =  fields.Selection(selection=[
            ('andalucia_este', 'Andalucía Este'),
            ('andorra', 'Andorra'),
            ('aragon', 'Aragón'),
            ('asturias_cantabria', 'Asturias y Cantabria'),
            ('balears', 'Balears'),
            ('canarias', 'Canarias'),
            ('castilla leon', 'Castilla León'),
            ('castilla la mancha', 'Castilla la Mancha'),
            ('catalunya', 'Catalunya'),
            ('extremadura', 'Extremadura'),
            ('madrid', 'Madrid'),
            ('navarra', 'Navarra y la Rioja'),
            ('pais_vasco', 'País Vasco')
        ], string='Región Comercial', readonly=True)
    
    def _select(self):
        return """
            SELECT
                m.id,
                l.create_date AS lead_create_date,
                l.date_conversion,
                l.date_deadline,
                l.date_closed,
                m.subtype_id,
                m.mail_activity_type_id,
                m.author_id,
                m.date,
                m.body,
                l.id as lead_id,
                l.user_id,
                l.team_id,
                l.country_id,
                l.company_id,
                l.stage_id,
                l.partner_id,
                rp.x_region_comercial,
                l.type as lead_type,
                l.active
        """

    def _from(self):
        return """
            FROM mail_message AS m
        """

    def _join(self):
        return """
            JOIN crm_lead AS l ON m.res_id = l.id
            left join res_partner AS rp ON l.partner_id = rp.id
        """