# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class account_discount_custom(models.Model):

    _inherit = 'account.move'

    x_discount_pp = fields.Float("Desc. PP %", default=0)
    x_discount_percent = fields.Float("Desc. %", default=0)


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(account_discount_custom, self)._onchange_partner_id()
        self.x_discount_pp = self.partner_id.x_descuento_pp
    
    @api.onchange('x_discount_pp','x_discount_percent')
    def onchange_discount(self):
        for record in self:
            for line in record.invoice_line_ids:
                if line.exclude_from_invoice_tab == False:
                    line._onchange_price_subtotal()
                    if line.price_subtotal > 0.0:
                        line._onchange_debit()
                    if line.price_subtotal < 0.0:
                        line._onchange_credit()
                    line._onchange_mark_recompute_taxes()
                    self._onchange_invoice_line_ids()


class account_line_discount_custom(models.Model):
    
    _inherit = 'account.move.line'

    discount_no_gobal = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    price_subtotal_no_global = fields.Monetary(string='Subtotal', store=True, readonly=True, currency_field='always_set_currency_id')

    # @api.onchange('discount_no_gobal', 'price_subtotal_no_global', 'move_id.x_discount_pp', 'move_id.x_discount_percent')
    @api.onchange('quantity', 'discount_no_gobal', 'price_unit', 'tax_ids')
    def _onchange_price_subtotal(self):
        
        self.discount = self.discount_no_gobal
        data_subtotal = self._get_price_total_and_subtotal()
        self.price_subtotal_no_global = data_subtotal['price_subtotal']
        self.discount = (self.discount or 0.0) + (self.move_id.x_discount_pp or 0.0) + (self.move_id.x_discount_percent or 0.0)

        super(account_line_discount_custom, self)._onchange_price_subtotal()
