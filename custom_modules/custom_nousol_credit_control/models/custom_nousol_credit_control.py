# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class custom_nousol_credit_control(models.Model):

    _inherit = 'res.partner'

    x_credit_control_fecha_inicio = fields.Date(string='Fecha Inicio')
    x_credit_control_fecha_fin = fields.Date(string='Fecha Fin')
    x_credit_control_observaciones = fields.Text(string='Observaciones')