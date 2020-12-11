# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class custom_nousol_product_pack(models.Model):

    _inherit = 'product.template'

    x_product_pack_get_data = fields.Integer(string='x_product_pack_get_data', compute = 'get_product_pack_data')
    
    #hacer un calculo al iniciar
    def get_product_pack_data(self):
        self.get_pack_product_data_change()
        self.x_product_pack_get_data = 0
    
    @api.onchange('pack_line_ids')
    def x_pack_line_onchange(self):
        #valores iniciales
        self.get_pack_product_data_change()
    
    def get_pack_product_data_change(self):
        #valores iniciales
        x_product_price = 0
        x_coste_price = 0
        x_total_weight = 0
        x_total_volumen = 0
        
        for line in self.pack_line_ids:        
            _logger.info('obtenemos datos')
            if(line.quantity > 0):
                x_product_price += line.product_id.list_price * line.quantity - (line.product_id.list_price * line.quantity * (line.sale_discount / 100))
                x_coste_price += line.product_id.standard_price * line.quantity
                x_total_weight += line.product_id.weight * line.quantity
                x_total_volumen += line.product_id.volume * line.quantity
            
        #actualizamos precio de venta
        self.list_price = x_product_price if x_product_price > 0 else self.list_price
        #actualizamos coste
        self.standard_price = x_coste_price if x_coste_price > 0 else self.standard_price
        #actualizamos peso
        self.weight = x_total_weight if x_total_weight > 0 else self.weight
        #actualizamos volumen
        self.volume = x_total_volumen if x_total_weight > 0 else self.volume