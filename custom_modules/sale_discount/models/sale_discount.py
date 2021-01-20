# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class sale_discount_custom(models.Model):

    _inherit = 'sale.order'

    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="['&','|', ('company_id', '=', False), ('company_id', '=', company_id), ('customer_rank', '>', 0)]",)

    x_discount_pp = fields.Float("Desc. PP %", default=0)
    x_discount_percent = fields.Float("Desc. %", default=0)


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(sale_discount_custom, self).onchange_partner_id()
        self.x_discount_pp = self.partner_id.x_descuento_pp

    @api.depends('order_line.price_total','x_discount_pp','x_discount_percent')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            #desc_pp = (order.x_discount_pp or 0.0)/100 #if (order.x_discount_pp or 0.0) > 1 else (order.x_discount_pp or 0.0)
            #desc_perc = (order.x_discount_percent or 0.0)/100 #if (order.x_discount_percent or 0.0) > 1 else (order.x_discount_percent or 0.0)
            desc = (order.x_discount_pp or 0.0)/100 + (order.x_discount_percent or 0.0)/100
            price_tax = 0
            price_total = 0
            price_subtotal = 0

            for line in order.order_line:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0 - desc)
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
                price_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                price_total += taxes['total_included']
                price_subtotal += taxes['total_excluded']
            order.update({
                'amount_untaxed': price_subtotal,
                'amount_tax': price_tax,
                'amount_total': price_subtotal + price_tax,
            })