from odoo import fields, models, api
import logging

_logger = logging.getLogger("prestashop")


class ProductProduct(models.Model):
    _inherit = "product.product"
    prestashop_product_variant_id = fields.Char("prestashop Product Variant ID", copy=False)
    prestashop_mapping_ids = fields.One2many("prestashop.product.detail", "product_id", string="Prestashop Mapping Table")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    prestashop_product = fields.Boolean('Prestashop Product')
    prestashop_product_id = fields.Char("prestashop product ID", copy=False)
    
    def create_prestashop_product_variant(self, attribute_ids=False):
        attribute_list = []
        attribute_and_value_list = []
        for attribute_value in attribute_ids:
            attribute_value_id = attribute_value.get('id')
            attribute_value_id = self.env['product.attribute.value'].search([('prestashop_attribute_value_id', '=', attribute_value_id)])
            if attribute_value_id and attribute_value_id.attribute_id:
                if attribute_value_id.attribute_id.id not in attribute_list:
                    attribute_list.append(attribute_value_id.attribute_id.id)
                attribute_and_value_list.append({'attribute_id': attribute_value_id.attribute_id.id, 'attribute_value_id': attribute_value_id.id})

        for attribute_id in attribute_list:
            product_attribute_values = []
            for attribute_and_value in attribute_and_value_list:
                if attribute_and_value.get('attribute_id') == attribute_id:
                    product_attribute_values.append(attribute_and_value.get('attribute_value_id'))
            if product_attribute_values:
                self.env['product.template.attribute.line'].create([{
                    'attribute_id': attribute_id,
                    'product_tmpl_id': self.id,
                    'value_ids': [(6, 0, product_attribute_values)]
                }])
        self.with_user(1)._create_variant_ids()

    def map_product_variant_id(self, prestashop_store_id=False,prod_id=False,stock_availables=False):
        api_operation = "http://%s@%s/api/combinations/?output_format=JSON&filter[id_product]=%s&display=full" % (
            prestashop_store_id and prestashop_store_id.prestashop_api_key,
            prestashop_store_id and prestashop_store_id.prestashop_api_url, prod_id)

        response_status, response_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(api_operation)
        if response_status:
            _logger.info("prestashop Get Product combinations Response : {0}".format(response_data))
            combinations = response_data.get('combinations')
            for combination in combinations:
                attribute_value_ids = []
                for attribute_value in combination.get('associations') and combination.get('associations').get('product_option_values'):
                    attribute_value_id = self.env['product.attribute.value'].search([('prestashop_attribute_value_id', '=', attribute_value.get('id'))], limit=1)
                    attribute_value_ids.append(attribute_value_id and attribute_value_id.name or "")

                    product_sku = combination.get('reference')
                    v_id = combination.get('id')

                    for product_variant_id in self.product_variant_ids:
                        if product_variant_id.mapped(lambda pv: pv.product_template_attribute_value_ids.mapped('name') == attribute_value_ids)[0]:
                            product_stock_id = False
                            for stock_available in stock_availables:
                                if v_id == int(stock_available.get('id_product_attribute')):
                                    product_stock_id = stock_available.get('id')
                            prestashop_product_detail = self.env['prestashop.product.detail'].create(
                                {'product_id': product_variant_id and product_variant_id.id,
                                 'prestashop_store_id': prestashop_store_id.id,
                                 'prestashop_product_id': prod_id,
                                 'product_combination_id': v_id,
                                 'product_stock_id' :product_stock_id and product_stock_id or "" })
                            product_variant_id.default_code = product_sku
                            product_variant_id.prestashop_product_variant_id = v_id

    def prestashop_to_odoo_import_product(self, warehouse_id=False, prestashop_store_id=False):
        req_data = False
        product_process_message = "Process Completed Successfully!"
        product_operation_id = self.env['prestashop.operation']
        if not product_operation_id:
            product_operation_id = prestashop_store_id.create_prestashop_operation('product', 'import', prestashop_store_id, 'Processing...')
        self._cr.commit()
        try:
            # api_operation = "http://%s@%s/api/products/?output_format=JSON&filter[id]=1169" % (
            api_operation = "http://%s@%s/api/products/?output_format=JSON" % (
            prestashop_store_id and prestashop_store_id.prestashop_api_key,
            prestashop_store_id and prestashop_store_id.prestashop_api_url)

            response_status, response_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(api_operation)
            if response_status:
                _logger.info("prestashop Get Product Response : {0}".format(response_data))
                products = response_data.get('products')
                for product in products:
                    prod_id = product.get('id')
                    if prod_id:
                        api_operation = "http://%s@%s/api/products/?output_format=JSON&resource=products&filter[id]=[%s]&display=full" % (
                            prestashop_store_id and prestashop_store_id.prestashop_api_key,
                            prestashop_store_id and prestashop_store_id.prestashop_api_url, prod_id)
                        response_status, product_response_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(api_operation)
                        if response_status:
                            product_dicts = product_response_data.get('products')
                            for product_dict in product_dicts:
                                product_ups = product_dict.get('reference')
                                product_id = False
                                if product_ups:
                                    product_id = self.env['product.product'].search([('default_code', '=', product_ups)], limit=1)
                                if not product_id:
                                    product_detail_id = self.env['prestashop.product.detail'].search([('prestashop_product_id', '=', product_dict.get('id'))], limit=1)
                                    product_id = product_detail_id and product_detail_id.product_id

                                template_title = product_dict.get('name')
                                category_ids = product_dict.get('associations') and product_dict.get('associations').get('categories')
                                attribute_ids = product_dict.get('associations') and product_dict.get('associations').get('product_option_values')
                                stock_availables = product_dict.get('associations') and product_dict.get('associations').get('stock_availables')
                                prestashop_category_id = False
                                if category_ids != None:
                                    for prestashop_category_id in category_ids:
                                        prestashop_category_id = prestashop_category_id.get('id')
                                category_id = self.env['product.category'].search([('prestashop_category_id', '=', prestashop_category_id)], limit=1)
                                if not category_id or not prestashop_category_id:
                                    process_message = "%s : Product Category Not Found In Odoo!" % (template_title)
                                    prestashop_store_id.create_prestashop_operation_detail('product', 'import', api_operation, product_response_data, product_operation_id, False, process_message)
                                    continue
                                template_title = prestashop_store_id.get_value_spanish(template_title)
                             
                                if not product_id:
                                    product_tmpl_id = self.create({
                                        'name': template_title,
                                        'type': 'product',
                                        'default_code':product_ups,
                                        'categ_id': category_id and category_id.id,
                                        "weight": product_dict.get("weight"),
                                        "list_price": product_dict.get("price"),
                                        'prestashop_product':True,
                                        'prestashop_product_id': prod_id
                                    })
                                    product_id = product_tmpl_id and product_tmpl_id.product_variant_id
                                    _logger.info("Product Created : {0}".format(product_tmpl_id.name))
                                    product_response_data = product_response_data
                                    process_message = "Product Created : {0}".format(product_tmpl_id.name)
                                else:
                                    product_tmpl_id = product_id and product_id.product_tmpl_id
                                    _logger.info("Product Already Exist : {0}".format(product_id.name))
                                    process_message = "Product Already Exist : {0}".format(product_id.name)
                                prestashop_store_id.create_prestashop_operation_detail('product', 'import', req_data, product_response_data, product_operation_id, False, process_message)
                                self._cr.commit()
                                if product_tmpl_id and attribute_ids and product_id.filtered(lambda pp: pp.with_user(1).product_variant_count <= 1):
                                    product_tmpl_id.create_prestashop_product_variant(attribute_ids)

                                    # Import Variant ID and set in perticular product id
                                    try:
                                        product_tmpl_id.map_product_variant_id(prestashop_store_id,prod_id,stock_availables)
                                    except Exception as e:
                                        _logger.info("Getting an Error In Import Product Combination Response {0} : {1}".format(e, product_id.name))
                                        process_message = "Getting an Error In Import Product Response {0} : {1}".format(e, product_id.name)
                                        prestashop_store_id.create_prestashop_operation_detail('product', 'import', False, False, product_operation_id, True, process_message)

                                if not self.env['prestashop.product.detail'].search([('prestashop_product_id', '=', product_dict.get('id')),('prestashop_store_id','=',prestashop_store_id.id)]):
                                    self.env['prestashop.product.detail'].create({
                                        'product_id': product_id and product_id.id,
                                        'prestashop_store_id': prestashop_store_id.id,
                                        'product_stock_id':stock_availables[0].get('id') if isinstance(stock_availables[0],dict) else "",
                                        'prestashop_product_id': prod_id})
                        else:
                            _logger.info("Getting an Error In Import Product Response {}".format(product_response_data))
                            product_response_data = product_response_data
                            process_message = "Getting an Error In Import Product Response".format(product_response_data)
                            prestashop_store_id.create_prestashop_operation_detail('product', 'import', req_data, product_response_data, product_operation_id, True, process_message)

                product_operation_id and product_operation_id.write({'prestashop_message': product_process_message})
                _logger.info("Import Product Process Completed ")
            else:
                _logger.info("Getting an Error In Import Product Response {}".format(response_data))
                response_data = response_data.content
                process_message = "Getting an Error In Import Product Response".format(response_data)
                prestashop_store_id.create_prestashop_operation_detail('product', 'import', req_data, response_data, product_operation_id, True, process_message)
        except Exception as e:
            product_process_message = "Process Is Not Completed Yet! %s" % (e)
            _logger.info("Getting an Error In Import Product Response {}".format(e))
            process_message = "Getting an Error In Import Product Response {}".format(e)
            prestashop_store_id.create_prestashop_operation_detail('product', 'import', response_data, product_process_message, product_operation_id, True, process_message)
        product_operation_id and product_operation_id.write({'prestashop_message': product_process_message})
        self._cr.commit()
