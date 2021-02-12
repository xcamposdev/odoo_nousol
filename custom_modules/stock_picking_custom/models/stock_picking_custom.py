# -*- coding: utf-8 -*-

import logging
import math
from math import log10
from collections import defaultdict, namedtuple
from odoo import api, fields, models, exceptions, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.date_utils import add, subtract
from odoo.tools.float_utils import float_round
import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class stock_picking_custom(models.Model):
    
    _inherit = 'stock.picking'

    x_carrier_tracking_ref = fields.Selection([
        ('opcion1', "Opcion 1"),
        ('opcion2', "Opcion 2"),
        ('opcion3', "Opcion 3"),
        ('opcion4', "Opcion 4"),
        ('opcion5', "Opcion 5"),
    ], default='', string="Referencia de seguimiento")

    @api.onchange('x_carrier_tracking_ref')
    def get_x_carrier_tracking_ref_onchange(self):
        self.carrier_tracking_ref = dict(self._fields['x_carrier_tracking_ref'].selection).get(self.x_carrier_tracking_ref)