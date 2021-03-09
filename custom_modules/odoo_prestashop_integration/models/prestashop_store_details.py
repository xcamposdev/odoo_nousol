import base64
import logging
from odoo import models, fields, api, _
from requests import request
import json

_logger = logging.getLogger("prestashop")


class prestashopCredentailDetails(models.Model):
    _name = "prestashop.store.details"

    name = fields.Char("Name", required=True, help="prestashop Store Configuration")
    prestashop_api_key = fields.Char("Prestashop API Key", required=True,
                                     help="Go in the PrestaShop back office, open the “Web service” page under the “Advanced Parameters” menu, and then choose “Yes” for the “Enable PrestaShop Webservice” option.")
    prestashop_api_url = fields.Char(string='Prestashop API URL', default="Your Store URL")

    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse")
    start_range = fields.Integer(string="Order ID Starting Range",help="Starting range for order import process", default=1)
    end_range = fields.Integer(string="Order ID Ending Range", help="Ending range for order import process", default=100)

    def create_prestashop_operation(self, operation, operation_type, prestashop_store_id, log_message):
        vals = {
            'prestashop_operation': operation,
            'prestashop_operation_type': operation_type,
            'prestashop_store_id': prestashop_store_id and prestashop_store_id.id,
            'prestashop_message': log_message,
        }
        operation_id = self.env['prestashop.operation'].create(vals)
        return operation_id

    def create_prestashop_operation_detail(self, operation, operation_type, req_data, response_data, operation_id,
                                            fault_operation=False, process_message=False):
        prestashop_operation_details_obj = self.env['prestashop.operation.details']
        vals = {
            'prestashop_operation': operation,
            'prestashop_operation_type': operation_type,
            'prestashop_request_message': '{}'.format(req_data),
            'prestashop_response_message': '{}'.format(response_data),
            'operation_id': operation_id.id,
            'fault_operation': fault_operation,
            'process_message': process_message,
        }
        operation_detail_id = prestashop_operation_details_obj.create(vals)
        return operation_detail_id


    def send_get_request_from_odoo_to_prestashop(self, api_operation=False):
        try:
            _logger.info("Prestashop API Request Data : %s" % (api_operation))
            data = "%s" % (self.prestashop_api_key)
            encode_data = base64.b64encode(data.encode("utf-8"))
            authrization_data = "Basic %s" % (encode_data.decode("utf-8"))
            headers = {"Authorization": "%s" % authrization_data}
            response_data = request(method='GET', url=api_operation, headers=headers)
            if response_data.status_code in [200, 201]:
                result = response_data.json()
                _logger.info("Prestashop API Response Data : %s" % (result))
                return True, result
            else:
                _logger.info("Prestashop API Response Data : %s" % (response_data.text))
                return False, response_data.text
        except Exception as e:
            _logger.info("Prestashop API Response Data : %s" % (e))
            return False, e


    def import_categories_from_prestashop(self):
        product_category_obj = self.env['product.category']
        product_category_obj.prestashop_to_odoo_import_product_categories(self.warehouse_id,self)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Product Categories Imported Successfully.",
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def import_products_from_prestashop(self):
        product_obj = self.env['product.template']
        product_obj.prestashop_to_odoo_import_product(self.warehouse_id, self)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Product Imported Successfully.",
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def import_order_from_prestashop(self):
        sale_order_obj = self.env['sale.order']
        sale_order_obj.prestashop_to_odoo_import_orders(self.warehouse_id, self)
        self.start_range = self.end_range
        self.end_range = self.end_range + 100
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Order Imported Successfully.",
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def import_product_attribute_from_prestashop(self):
        product_attribute_obj = self.env['product.attribute']
        product_attribute_obj.prestashop_to_odoo_import_product_attribute(self.warehouse_id, self)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Product Attribute Imported Successfully.",
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def import_product_stock_from_prestashop(self):
        product_stock_obj = self.env['stock.inventory']
        product_stock_obj.prestashop_to_odoo_import_stock_inventory(self.warehouse_id, self)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Product Imported Successfully.",
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def action_view_prestashop_categories(self):
        action = self.env.ref('product.product_category_action_form').read()[0]
        action['domain'] = [('prestashop_category_id', '!=', False)]
        return action

    def action_view_prestashop_product(self):
        action = self.env.ref('sale.product_template_action').read()[0]
        action['domain'] = [('prestashop_product', '!=', False)]
        return action

    def action_view_prestashop_product_detail(self):
        action = self.env.ref('product.product_normal_action_sell').read()[0]
        action['domain'] = [('prestashop_mapping_ids', '!=', False)]
        return action

    def action_view_prestashop_customers(self):
        action = self.env.ref('base.action_partner_form').read()[0]
        action['domain'] = [('prestashop_store_id', '=',self.id)]
        action['context'] = {'default_prestashop_store_id': self.id}
        return action

    def action_view_prestashop_orders(self):
        action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
        action['domain'] = [('prestashop_store_id', '=', self.id)]
        action['context'] = {'default_prestashop_store_id': self.id}
        return action

    def action_view_prestashop_message_detail(self):
        action = self.env.ref('odoo_prestashop_integration.action_prestashop_operation').read()[0]
        action['context'] = {'default_prestashop_store_id': self.id}
        return action

    
    def get_value_spanish(self, name):
        data_find = list(_data for _data in name if _data['id'] == '1')
        return data_find[0]['value']