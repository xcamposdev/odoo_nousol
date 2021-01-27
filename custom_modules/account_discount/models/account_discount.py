# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons.account.models.account_move import AccountMoveLine

_logger = logging.getLogger(__name__)

INTEGRITY_HASH_LINE_FIELDS = ('debit', 'credit', 'account_id', 'partner_id')

class account_discount_custom(models.Model):

    _inherit = 'account.move'

    x_discount_pp = fields.Float("Desc. PP %", default=0)
    x_discount_percent = fields.Float("Desc. %", default=0)


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(account_discount_custom, self)._onchange_partner_id()
        if self._context.get('active_model', False) != 'purchase.order':
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

    x_discount_no_global = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    x_price_subtotal_no_global = fields.Monetary(string='Subtotal', store=True, readonly=True, currency_field='always_set_currency_id')

    @api.onchange('quantity', 'x_discount_no_global', 'price_unit', 'tax_ids')
    def _onchange_price_subtotal(self):
        for record in self:
            record.discount = record.x_discount_no_global
            record.x_price_subtotal_no_global = record._get_price_total_and_subtotal()['price_subtotal']

            record.discount = (record.discount or 0.0) + (record.move_id.x_discount_pp or 0.0) + (record.move_id.x_discount_percent or 0.0)
            super(account_line_discount_custom, record)._onchange_price_subtotal()
