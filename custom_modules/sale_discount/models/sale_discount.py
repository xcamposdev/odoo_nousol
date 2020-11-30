# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class sale_discount_custom(models.Model):

    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(sale_discount_custom, self).onchange_partner_id()
        self.create_descount_line()

    def create_descount_line(self):
        config_descuento_comercial = self.env['ir.config_parameter'].sudo().get_param('x_producto_descuento_comercial')
        config_descuento_pp = self.env['ir.config_parameter'].sudo().get_param('x_producto_descuento_pp')
        config_descuento_portes = self.env['ir.config_parameter'].sudo().get_param('x_producto_descuento_portes')

        # Add or Update line
        if(self.order_line):
            product_descuento_comercial = self.env['product.product'].search([('name','=',config_descuento_comercial)], limit=1)
            if self.partner_id.x_descuento_comercial > 0 and product_descuento_comercial:
                self.add_update_line(product_descuento_comercial.id, self.partner_id.x_descuento_comercial)
            
            product_descuento_pp = self.env['product.product'].search([('name','=',config_descuento_pp)], limit=1)
            if self.partner_id.x_descuento_pp > 0 and product_descuento_pp:
                self.add_update_line(product_descuento_pp.id, self.partner_id.x_descuento_pp)

            product_descuento_portes = self.env['product.product'].search([('name','=',config_descuento_portes)], limit=1)
            if self.partner_id.x_descuento_portes > 0 and product_descuento_portes:
                self.add_update_line(product_descuento_portes.id, self.partner_id.x_descuento_portes)


    def add_update_line(self, product_id, amount):
        order_line = list(line for line in self.order_line if line.product_id.id == product_id)
        if(not order_line):
            self.order_line = [(0,0, {
                'product_id': product_id
            })]
            self.order_line[-1].product_id_change()
            self.order_line[-1].name = self.order_line[-1].product_id.name + " " + str(amount) + "%"
        else:
            self.order_line.name = self.order_line[-1].product_id.name + " " + str(amount) + "%"

    
    # @api.onchange('order_line')
    # def _onchange_order_line_subtotal(self):
    #     _subtotal = 0
    #     _discount1 = 0
    #     _is_section_descount = False

    #     items = []
    #     section_now = ""
    #     for line in self.order_line:
    #         # Calcula el precio de descuento
    #         if(line.display_type == 'line_section' and _is_section_descount == True):
    #             _is_section_descount = False
    #         if(line.display_type == 'line_section' and line.name.lower().encode('utf-8') == self.SECTION_DESCUENTOS.lower().encode('utf-8')):
    #             _is_section_descount = True
    #         if not _is_section_descount:
    #             _subtotal += abs(line.price_subtotal)
    #         else:
    #             if(line.product_id and line.product_id.id == self.PRODUCT_DISCOUNT_1_ID and self.partner_id.id != False):
    #                 price_discount = (_subtotal * self.partner_id.x_studio_descuento_comercial)/100
    #                 line.update({'price_unit': price_discount*(-1)})
    #                 _discount1 = _subtotal - price_discount
    #             if(line.product_id and line.product_id.id == self.PRODUCT_DISCOUNT_2_ID and self.partner_id.id != False):
    #                 price_discount2 = (_discount1 * self.partner_id.x_studio_descuento_pp)/100
    #                 line.update({'price_unit': price_discount2*(-1)})

    #         # PRODUCT_MERMA_NAME
    #         if(_is_section_descount == False):
                
    #             if(line.display_type == 'line_section'):
    #                 section_now = line.name

    #             if(line.product_id.id != False and line.product_id.id != self.PRODUCT_MERMA_ID and line.display_type == False):
    #                 _pos = -1
    #                 _m2t = line.x_studio_tablas * (line.product_id.x_studio_largo_cm/100) * (line.product_id.x_studio_alto_cm/100)
    #                 for pos in range(len(items)):
    #                     if(items[pos]['product_id'] == line.product_id.id):
    #                         _pos = pos
    #                         break

    #                 if(int(_pos) == int(-1)):
    #                     items.append({
    #                         'product_id': line.product_id.id,
    #                         'product_name': line.product_id.name, 
    #                         'tablas': line.x_studio_tablas, 
    #                         'm2t': _m2t, 
    #                         'm2u': line.product_uom_qty, 
    #                         'price': line.product_id.standard_price,
    #                         'section': section_now
    #                         })
    #                 else:
    #                     items[_pos]['tablas'] = line.x_studio_tablas + items[_pos]['tablas']
    #                     items[_pos]['m2t'] = _m2t + items[_pos]['m2t']
    #                     items[_pos]['m2u'] = line.product_uom_qty + items[_pos]['m2u']
    #                     items[_pos]['section'] = section_now

    #     for merma in items:
    #         if(merma['tablas'] > 0):
    #             pos_new_record = self.check_if_exists_merma_product(self.PRODUCT_MERMA_ID, merma['product_name'])
    #             if(int(pos_new_record) == int(-1)):
    #                 pos_new_record = self.create_product_in_order_line(merma['section']) + 1
    #                 self.order_line[pos_new_record].product_id = self.PRODUCT_MERMA_ID
    #                 self.order_line[pos_new_record].product_id_change()
    #             self.order_line[pos_new_record].name = self.PRODUCT_MERMA_NAME + ": " + merma['product_name']
    #             self.order_line[pos_new_record].product_uom_qty = merma['m2t'] - merma['m2u']
    #             self.order_line[pos_new_record].price_unit = merma['price']
                    
    # def check_if_exists_merma_product(self, merma_id, product_name):
    #     pos_found = -1
    #     if(self.order_line):
    #         for pos in range(len(self.order_line)):
    #             description_name = self.PRODUCT_MERMA_NAME + ": " + product_name
    #             if(self.order_line[pos].product_id.id == merma_id and self.order_line[pos].name.lower().encode('utf-8') == description_name.lower().encode('utf-8')):
    #                 pos_found = pos
    #                 break
    #     return pos_found
    