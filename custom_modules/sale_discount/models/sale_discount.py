# -*- coding: utf-8 -*-

import logging
from itertools import groupby
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare

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
        #self.x_discount_percent = self.partner_id.x_descuento_comercial


    @api.depends('order_line.price_total','x_discount_pp','x_discount_percent')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            desc = (order.x_discount_pp or 0.0)/100 + (order.x_discount_percent or 0.0)/100
            price_tax = 0
            price_total = 0
            price_subtotal = 0
            
            for line in order.order_line:
                price = (line.price_unit * (1 - (line.discount or 0.0) / 100.0)) * (1 - desc)
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
                
                price_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                price_total += taxes['total_included']
                price_subtotal += taxes['total_excluded']
                
            order.update({
                'amount_untaxed': price_subtotal,
                'amount_tax': price_tax,
                'amount_total': price_subtotal + price_tax,
            })

    def _create_invoices(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Create invoices.
        invoice_vals_list = []
        for order in self:
            pending_section = None

            # Invoice values.
            invoice_vals = order._prepare_invoice()

            #############
            invoice_vals['x_discount_pp'] = self.x_discount_pp
            invoice_vals['x_discount_percent'] = self.x_discount_percent
            #############

            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_invoice_line()))
                        pending_section = None
                    
                    ######################################
                    line_new = line._prepare_invoice_line()
                    line_new['discount'] = (line.discount or 0.0)
                    ######################################

                    invoice_vals['invoice_line_ids'].append((0, 0, line_new))

            if not invoice_vals['invoice_line_ids']:
                raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['invoice_payment_ref'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'invoice_payment_ref': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_type='out_invoice').create(invoice_vals_list)
        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                subtype_id=self.env.ref('mail.mt_note').id
            )
        return moves


class sale_modal_create_factura(models.TransientModel):

    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, name, amount, so_line):
        line = self.env['sale.order.line'].search([('id','=',so_line.id)])
        invoice_vals = {
            'ref': order.client_order_ref,
            'type': 'out_invoice',
            'invoice_origin': order.name,
            'invoice_user_id': order.user_id.id,
            'narration': order.note,
            'partner_id': order.partner_invoice_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'currency_id': order.pricelist_id.currency_id.id,
            'invoice_payment_ref': order.reference,
            'invoice_payment_term_id': order.payment_term_id.id,
            'invoice_partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            'team_id': order.team_id.id,
            'campaign_id': order.campaign_id.id,
            'medium_id': order.medium_id.id,
            'source_id': order.source_id.id,
            'x_discount_pp': order.x_discount_pp,
            'x_discount_percent': order.x_discount_percent,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': (order.x_discount_pp or 0.0) + (order.x_discount_percent or 0.0) + (line.discount or 0.0),
                'x_discount_no_global': line.discount,
                'product_id': self.product_id.id,
                'product_uom_id': so_line.product_uom.id,
                'tax_ids': [(6, 0, so_line.tax_id.ids)],
                'sale_line_ids': [(6, 0, [so_line.id])],
                'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'analytic_account_id': order.analytic_account_id.id or False,
            })],
        }

        return invoice_vals