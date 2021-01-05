# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class product_discount_custom(models.Model):

    _inherit = 'product.template'

    x_alto = fields.Float(string="Alto (m)", default=0)
    x_largo = fields.Float(string="Largo (m)", default=0)
    x_ancho = fields.Float(string="Ancho (m)", default=0)


    def get_product_multiline_description_sale(self):
        """ Compute a multiline description of this product, in the context of sales
                (do not use for purchases or other display reasons that don't intend to use "description_sale").
            It will often be used as the default description of a sale order line referencing this product.
        """
        name = self.display_name
        if self.description_sale:
            name = self.description_sale
            #name += '\n' + self.description_sale

        return name