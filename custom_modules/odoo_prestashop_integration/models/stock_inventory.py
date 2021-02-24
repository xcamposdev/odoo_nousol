from odoo import fields, models
import logging
import datetime

_logger = logging.getLogger("prestashop")


class PrestashopStockInventory(models.Model):
    _inherit = "stock.inventory"

    def prestashop_to_odoo_import_stock_inventory(self, warehouse_id=False, prestashop_store_id=False):
        product_process_message = "Process Completed Successfully!"
        self._cr.commit()
        product_detail_ids = self.env['prestashop.product.detail'].search([])
        product_operation_id = prestashop_store_id.create_prestashop_operation('stock', 'import',
                                                                               prestashop_store_id,
                                                                               'Processing...')
        try:
            stock_inventory_id = self.env['stock.inventory'].create({
                'name': '%s' % (datetime.datetime.now()),
                'prefill_counted_quantity': 'zero',
            })
            product_ids = []
            inventory_lines = []
            for product_detail_id in product_detail_ids:
                _logger.info("Product detail id {}".format(product_detail_id.id))
                if product_detail_id.product_combination_id:
                    api_operation = "http://%s@%s/api/stock_availables/?output_format=JSON&filter[id_product_attribute]=[%s]&display=full" % (
                        prestashop_store_id and prestashop_store_id.prestashop_api_key,
                        prestashop_store_id and prestashop_store_id.prestashop_api_url,
                        product_detail_id.product_combination_id)
                else:
                    # True
                    api_operation = "http://%s@%s/api/stock_availables/?output_format=JSON&filter[id_product]=[%s]&display=full" % (
                        prestashop_store_id and prestashop_store_id.prestashop_api_key,
                        prestashop_store_id and prestashop_store_id.prestashop_api_url,
                        product_detail_id.prestashop_product_id)

                response_status, response_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(
                    api_operation)
                if response_status:
                    _logger.info("prestashop Get Product Response : {0}".format(response_data))
                    product_stock_inventory = response_data.get('stock_availables') if response_data else []

                    for stock_inventory in product_stock_inventory:
                        quantity = "{}".format(stock_inventory.get('quantity'))
                        if product_detail_id and product_detail_id.product_id.id:
                            product_ids.append(product_detail_id and product_detail_id.product_id.id)
                        else:
                            continue
                        inventory_lines.append((0, 0, {
                            'inventory_id': stock_inventory_id.id,
                            'product_qty': quantity,
                            'product_id': product_detail_id and product_detail_id.product_id.id,
                            'location_id': prestashop_store_id.warehouse_id.lot_stock_id.id
                        }))
                        prestashop_store_id.create_prestashop_operation_detail('stock', 'import',
                                                                               api_operation,
                                                                               response_data,
                                                                               product_operation_id,
                                                                               False,
                                                                               product_stock_inventory)
                else:
                    process_message = "Import Product Stock Failed %s"%(product_detail_id and product_detail_id.product_id.name)
                    prestashop_store_id.create_prestashop_operation_detail('stock', 'import',
                                                                           api_operation,
                                                                           response_data,
                                                                           product_operation_id,
                                                                           True,
                                                                           process_message)

            stock_inventory_id.write({
                'product_ids': product_ids,
                'line_ids': inventory_lines,
            })
            stock_inventory_id.action_start()
            stock_inventory_id.action_validate()

        except Exception as e:
            _logger.info("Getting an Error In Import Product Stock Response {}".format(e))
            process_message = "Getting an Error In Import Product Stock Response {}".format(e)
            prestashop_store_id.create_prestashop_operation_detail('stock', 'import',
                                                                   api_operation,
                                                                   response_data,
                                                                   product_operation_id,
                                                                   True,
                                                                   process_message)

        product_operation_id and product_operation_id.write({'prestashop_message': product_process_message})
        self._cr.commit()
