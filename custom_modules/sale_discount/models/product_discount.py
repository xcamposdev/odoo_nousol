# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class product_discount_custom(models.Model):

    _inherit = 'product.template'

    x_alto = fields.Float(string="Alto (m)", default=0)
    x_largo = fields.Float(string="Largo (m)", default=0)
    x_ancho = fields.Float(string="Ancho (m)", default=0)
