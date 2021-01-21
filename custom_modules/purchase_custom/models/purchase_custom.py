# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class purchase_custom(models.Model):

    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    partner_id = fields.Many2one('res.partner', string='Proveedor', required=True, states=READONLY_STATES, change_default=True, tracking=True, 
        domain="['&','|', ('company_id', '=', False), ('company_id', '=', company_id), ('supplier_rank','>',0)]", 
        help="Puede encontrar un proveedor por su nombre, NIF, correo electrónico o referencia interna.")
