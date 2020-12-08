# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class custom_nousol_credit_control(models.Model):

    _inherit = 'res.partner'
    test = ''
    