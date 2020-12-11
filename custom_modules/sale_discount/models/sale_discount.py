# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class sale_discount_custom(models.Model):

    _inherit = 'sale.order'

    
    product_descuento_comercial = fields.Many2one("product.product", store=False, default=lambda self: self.env['product.product'].search(\
        [('name','=',self.env['ir.config_parameter'].sudo().get_param('x_producto_descuento_comercial'))], limit=1))
    product_descuento_pp = fields.Many2one("product.product", store=False, default=lambda self: self.env['product.product'].search(\
        [('name','=',self.env['ir.config_parameter'].sudo().get_param('x_producto_descuento_pp'))], limit=1))

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(sale_discount_custom, self).onchange_partner_id()
        self.crud_discount_line(self.product_descuento_comercial, self.partner_id.x_descuento_comercial)
        self.crud_discount_line(self.product_descuento_pp, self.partner_id.x_descuento_pp)

    def crud_discount_line(self, product_id, amount_discount):
        if product_id:
            order_line = list(line for line in self.order_line if line.product_id.id == product_id.id)
            if not order_line and amount_discount > 0: #Add
                self.order_line = [(0,0, {
                    'product_id': product_id.id
                })]
                self.order_line[-1].product_id_change()
                self.order_line[-1].name = self.order_line[-1].product_id.name + " " + str(amount_discount) + "%"
            elif order_line and amount_discount > 0: #Edit
                order_line[0].product_id_change()
                order_line[0].name = order_line[0].product_id.name + " " + str(amount_discount) + "%"
            elif order_line and amount_discount == 0: #Delete
                self.order_line = [(2,order_line[0].id)]

    # @api.onchange('order_line')
    # def onchange_amount_all(self):
    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            subtotal = 0
            for line in self.order_line:
                if (self.product_descuento_comercial and self.product_descuento_comercial.id != line.product_id.id) and \
                    (self.product_descuento_pp and self.product_descuento_pp.id != line.product_id.id):
                    subtotal += line.price_subtotal
            
            if self.product_descuento_comercial:
                order_line = list(line for line in self.order_line if line.product_id.id == self.product_descuento_comercial.id)
                if(order_line):
                    discount = (subtotal * self.partner_id.x_descuento_comercial)/100
                    order_line[0].update({'price_unit': discount * (-1)})
                    #order_line[0].price_unit = discount * (-1)
                    subtotal = subtotal - discount
            if self.product_descuento_pp:
                order_line = list(line for line in self.order_line if line.product_id.id == self.product_descuento_pp.id)
                if order_line:
                    discount = (subtotal * self.partner_id.x_descuento_pp)/100
                    order_line[0].update({'price_unit': discount * (-1)})
                    #order_line[0].price_unit = discount * (-1)
                    subtotal = subtotal - discount
        super(sale_discount_custom, self)._amount_all()