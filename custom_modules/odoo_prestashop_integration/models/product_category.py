from odoo import fields, models, api
import logging

_logger = logging.getLogger("prestashop")

class ProductCategory(models.Model):
    _inherit = "product.category"

    prestashop_category_url = fields.Char(string="Custom Url", copy=False)
    prestashop_parent_category_id = fields.Char("prestashop Parent Category ID", copy=False)
    prestashop_category_id = fields.Char("prestashop Category ID", copy=False)

    def prestashop_to_odoo_import_product_categories(self,warehouse_id=False, prestashop_store_id=False):
        req_data = False
        category_process_message = "Process Completed Successfully!"
        category_operation_id = self.env['prestashop.operation']
        if not category_operation_id:
            category_operation_id = prestashop_store_id.create_prestashop_operation('product_category','import',prestashop_store_id,'Processing...')
        self._cr.commit()
        try:
            api_operation = "http://%s@%s/api/categories/?output_format=JSON"%(prestashop_store_id and prestashop_store_id.prestashop_api_key,prestashop_store_id and prestashop_store_id.prestashop_api_url)

            response_status, response_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(api_operation)
            if response_status:
                _logger.info("prestashop Get Product Category Response : {0}".format(response_data))
                categories = response_data.get('categories')
                for category in categories:
                    categ_id = category.get('id')
                    if categ_id:
                        api_operation = "http://%s@%s/api/categories/?output_format=JSON&resource=categories&filter[id]=[%s]&display=full" % (
                        prestashop_store_id and prestashop_store_id.prestashop_api_key,
                        prestashop_store_id and prestashop_store_id.prestashop_api_url,categ_id)

                        response_status, response_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(
                            api_operation)

                        if response_status:
                            for category in response_data.get('categories'):
                                category_id = self.env['product.category'].search(
                                    [('prestashop_category_id', '=', category.get('id'))], limit=1)
                                parent_id_res = category.get('id_parent')
                                if not category_id:
                                    vals = {
                                        'name': category.get('name'),
                                        'prestashop_category_url': category.get('link_rewrite'),
                                        'prestashop_parent_category_id': parent_id_res,
                                        'property_cost_method': 'standard',
                                        'property_valuation': 'manual_periodic',
                                        'prestashop_category_id': category.get('id'),
                                    }
                                    category_id = self.env['product.category'].create(vals)
                                    _logger.info("Product Category Created : {0}".format(category_id.name))
                                    response_data = response_data
                                    process_message = "Product Category Created : {0}".format(category_id.name)
                                else:
                                    vals = {
                                        'name': category.get('name'),
                                        'prestashop_category_url': category.get('link_rewrite'),
                                        'prestashop_parent_category_id': parent_id_res,
                                        'property_cost_method': 'standard',
                                        'property_valuation': 'manual_periodic',
                                        'prestashop_category_id': category.get('id'),
                                    }
                                    category_id.write(vals)
                                    _logger.info("Product Category Updated : {0}".format(category_id.name))
                                    process_message = "Product Category Updated : {0}".format(category_id.name)
                                prestashop_store_id.create_prestashop_operation_detail('product_category', 'import', req_data,
                                                                            response_data, category_operation_id,
                                                                            False, process_message)
                                self._cr.commit()
                        else:
                            _logger.info(
                                "Getting an Error In Import Product Category Response {}".format(response_data))
                            response_data = response_data.content
                            process_message = "Getting an Error In Import Product Category Response".format(
                                response_data)
                            prestashop_store_id.create_prestashop_operation_detail('product_category', 'import', req_data,
                                                                    response_data, category_operation_id,
                                                                    True, process_message)

                category_ids = self.env['product.category'].search([('prestashop_category_id', '!=', False),('prestashop_parent_category_id','!=',False)])
                if category_ids:
                    for c_id in category_ids:
                        parent_id = self.env['product.category'].search([('prestashop_category_id', '=', c_id.prestashop_parent_category_id)], limit=1)
                        c_id.parent_id = parent_id and parent_id.id

                category_operation_id and category_operation_id.write(
                    {'prestashop_message': category_process_message})
                _logger.info("Import Product Category Process Completed ")
            else :
                _logger.info("Getting an Error In Import Product Category Response {}".format(response_data))
                response_data = response_data.content
                process_message = "Getting an Error In Import Product Category Response".format(response_data)
                prestashop_store_id.create_prestashop_operation_detail('product_category', 'import', req_data, response_data,
                                                        category_operation_id, True, process_message)
        except Exception as e:
            category_process_message = "Process Is Not Completed Yet! %s" % (e)
            _logger.info("Getting an Error In Import Product Category Response {}".format(e))
            process_message="Getting an Error In Import Product Category Response {}".format(e)
            prestashop_store_id.create_prestashop_operation_detail('product_category','import',response_data,category_process_message,category_operation_id,True,process_message)
        category_operation_id and category_operation_id.write({'prestashop_message': category_process_message})
        self._cr.commit()
