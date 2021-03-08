from odoo import models, fields, api
import xml.etree.ElementTree as etree
import requests
import logging
import base64
import json
import io
#from io import BytesIO

_logger = logging.getLogger("prestashop")

class ExportProductPrestashop(models.Model):
    
    _inherit = "product.template"

    @api.model
    def create(self, vals_list):
        data = super(ExportProductPrestashop, self).create(vals_list)
        ################################################################
        self._cr.commit()
        try:
            self = data
            self.products_sincronize('POST')
        except Exception as e:
            _logger.info("Error al importar en prestashop {}".format(e))
        ################################################################
        return data

    def write(self, values, sincronize=True):
        data = super(ExportProductPrestashop, self).write(values)
        ################################################################
        self._cr.commit()
        try:
            self = self.env['product.template'].search([('id','=',self.id)])
            if sincronize == True:
                self.products_sincronize('PUT')
        except Exception as e:
            _logger.info("Error al importar en prestashop {}".format(e))
        ################################################################
        return data
    
    def unlink(self):
        for record in self:
            prestashop_product_id = record.prestashop_product_id if record.prestashop_product_id else False
            data = super(ExportProductPrestashop, record).unlink()
            ################################################################
            self._cr.commit()
            try:
                if prestashop_product_id:
                    self.product_delete(prestashop_product_id)
            except Exception as e:
                _logger.info("Error al importar en prestashop {}".format(e))
            ################################################################
        return data
    
    def products_sincronize(self, operation):
        if(self.id):
            self.ensure_one()
            prestashop_store_id = self.env['prestashop.store.details'].search([('id', '!=', False)])
            api_operation = "http://%s@%s/api/languages/?output_format=JSON&display=full" % (
                            prestashop_store_id and prestashop_store_id.prestashop_api_key,
                            prestashop_store_id and prestashop_store_id.prestashop_api_url)

            service_root = etree.Element("prestashop")
            request = etree.SubElement(service_root, "products")
            name_tree =  etree.SubElement(request, "name")
            description = etree.SubElement(request, "description")
            description_short = etree.SubElement(request, "description_short")
            link_rewrite = etree.SubElement(request, "link_rewrite")

            if(operation == 'PUT'):
                etree.SubElement(request, 'id').text ="%s"%(self.prestashop_product_id)

            response_status, languages_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(api_operation)
            languages = languages_data.get('languages')            

            if(response_status and len(languages) > 0):
                for language in languages:
                    lan_id = language.get('id')

                    etree.SubElement(name_tree, "language", id = "%s"%(lan_id)).text ="%s"%(self.name)
                    etree.SubElement(link_rewrite, "language", id = "%s"%(lan_id)).text ="%s"%(self.name.replace(" ", "-"))
                    etree.SubElement(description, "language", id = "%s"%(lan_id)).text ="%s"%(self.description_sale if self.description_sale else '')
                    etree.SubElement(description_short, "language", id = "%s"%(lan_id)).text ="%s"%(self.description_sale if self.description_sale else '')
            else:
                etree.SubElement(name_tree, "language", id = "0").text ="%s"%(self.name)
                etree.SubElement(link_rewrite, "language", id = "0").text ="%s"%(self.name.replace(" ", "-"))
                etree.SubElement(description, "language", id = "0").text ="%s"%(self.description_sale if self.description_sale else '')
                etree.SubElement(description_short, "language", id = "0").text ="%s"%(self.description_sale if self.description_sale else '')
            
            if(self.categ_id.id):
                cat_name = 'inicio' if self.categ_id.name == 'All' else self.categ_id.name
                ap_operation = "http://%s@%s/api/categories/?output_format=JSON&resource=categories&filter[name]=[%s]&limit=1&display=full" % (
                            prestashop_store_id and prestashop_store_id.prestashop_api_key,
                            prestashop_store_id and prestashop_store_id.prestashop_api_url, cat_name) 
                ap_response, parent_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(ap_operation)
                
                if(ap_response and len(parent_data) > 0):
                    parent_categories = parent_data.get('categories')
                    for cat in parent_categories:
                        parent_id = cat.get('id')
                        etree.SubElement(request, "id_category_default").text = "%s"%(int(parent_id))

            etree.SubElement(request, "price").text ="%s"%(self.list_price)
            etree.SubElement(request, "advanced_stock_management").text = "0"
            etree.SubElement(request, "low_stock_alert").text = "0"
            etree.SubElement(request, "minimal_quantity").text = "1"
            etree.SubElement(request, "available_for_order").text = "1"
            etree.SubElement(request, "active").text = "0"
            etree.SubElement(request, "reference").text ="%s"%(self.default_code if self.default_code else '')

            etree.dump(service_root)

            data = "%s" % (prestashop_store_id.prestashop_api_key)
            encode_data = base64.b64encode(data.encode("utf-8"))
            authrization_data = "Basic %s" % (encode_data.decode("utf-8"))
            headers = {"Content-Type": "application/xml","Authorization": "%s" % authrization_data}
            url = "http://%s@%s/api/products/?output_format=JSON&resource=products" % (
                prestashop_store_id and prestashop_store_id.prestashop_api_key,
                prestashop_store_id and prestashop_store_id.prestashop_api_url)
            try:
                xml= etree.tostring(service_root)
                response_body = requests.request(operation, url=url, data=xml, headers=headers)
                if response_body.status_code in [200, 201]:
                    response_body = response_body.json()
                    id_prod = response_body.get('product').get('id')

                    # una vez creado el producto actualizamos su id de prestashop
                    self.write({
                        'prestashop_product': True,
                        'prestashop_product_id': id_prod
                    }, sincronize=False)

                    # agregamos la imagen en caso de que exista al producto ya creado    
                    if (id_prod and self.image_1920):
                        headers = {"Authorization": "%s" % authrization_data}
                        url_prod = "http://%s@%s/api/images/products/%s" % (
                                        prestashop_store_id and prestashop_store_id.prestashop_api_key,
                                        prestashop_store_id and prestashop_store_id.prestashop_api_url, id_prod)

                        _files = { 'image': ('imagen1.png', base64.b64decode(self.image_1920), 'image/png') }
                        #_files = { 'image': ('imagen1.png', open('C:/Users/Administrador/Downloads/imagen.png','rb'), 'image/png') }
                        response_prod = requests.request(operation, url=url_prod, headers=headers, data={}, files=_files)

                        _logger.info("Prestashop API Response Data : %s" % (response_body))
                    return True
                else:
                    _logger.info("Prestashop API Response Data : %s" % (response_body.text))
                    return False
            except Exception as e:
                _logger.info("Prestashop API Response Data : %s" % (e))
                return False, e


    def product_delete(self, id_prod):
        if(id_prod):
            prestashop_store_id = self.env['prestashop.store.details'].search([('id', '!=', False)])
            data = "%s" % (prestashop_store_id.prestashop_api_key)
            encode_data = base64.b64encode(data.encode("utf-8"))
            authrization_data = "Basic %s" % (encode_data.decode("utf-8"))
            headers = {"Content-Type": "application/xml","Authorization": "%s" % authrization_data}
            url = "http://%s@%s/api/products/%s/?output_format=JSON" % (
                prestashop_store_id and prestashop_store_id.prestashop_api_key,
                prestashop_store_id and prestashop_store_id.prestashop_api_url, id_prod)
            try:
                response_body = requests.request('DELETE', url=url, headers=headers)
                if response_body.status_code in [200, 201]:
                    _logger.info("Prestashop API Response Data : %s" % (response_body))
                    return True
                else:
                    _logger.info("Prestashop API Response Data : %s" % (response_body.text))
                    return False
            except Exception as e:
                _logger.info("Prestashop API Response Data : %s" % (e))
                return False, e
