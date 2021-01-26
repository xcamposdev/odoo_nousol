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

    x_discount_pp = fields.Float("Desc. PP %", default=0)
    x_discount_percent = fields.Float("Desc. %", default=0)


    @api.depends('order_line.price_total','x_discount_pp','x_discount_percent')
    def _amount_all(self):
        for order in self:
            desc = (order.x_discount_pp or 0.0)/100 + (order.x_discount_percent or 0.0)/100
            price_tax = price_total = price_subtotal = 0
            for line in order.order_line:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0 - desc)
                taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
                price_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                price_total += taxes['total_included']
                price_subtotal += taxes['total_excluded']
            order.update({
                'amount_untaxed': price_subtotal,
                'amount_tax': price_tax,
                'amount_total': price_subtotal + price_tax,
            })
