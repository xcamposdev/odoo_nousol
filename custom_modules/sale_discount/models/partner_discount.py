# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class partner_discount_custom(models.Model):

    _inherit = 'res.partner'

    x_descuento_comercial = fields.Float(string="Descuento Comercial", default=0)
    x_descuento_pp = fields.Float(string="Descuento PP", default=0)
    x_transportista = fields.Many2one('res.partner', string="Transportista")