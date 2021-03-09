from odoo import models, fields, api
import xml.etree.ElementTree as etree
import requests
import logging
import base64

_logger = logging.getLogger("prestashop")

class ExportProductCategoryPrestashop(models.Model):
    
    _inherit = "product.category"
    
    @api.model
    def create(self, vals_list):
        data = super(ExportProductCategoryPrestashop, self).create(vals_list)
        ################################################################
        prestashop_crud = self.env['ir.config_parameter'].sudo().get_param('x_prestashop_crud')
        if int(prestashop_crud):
            self._cr.commit()
            try:
                self = data
                self.categories_sincronize('POST')
            except Exception as e:
                _logger.info("Error al importar en prestashop {}".format(e))
        ################################################################
        return data

    def write(self, values, sincronize=True):
        data = super(ExportProductCategoryPrestashop, self).write(values)
        ################################################################
        prestashop_crud = self.env['ir.config_parameter'].sudo().get_param('x_prestashop_crud')
        if int(prestashop_crud):
            self._cr.commit()
            try:
                self = self.env['product.category'].search([('id','=',self.id)])
                if sincronize == True:
                    self.categories_sincronize('PUT')
            except Exception as e:
                _logger.info("Error al importar en prestashop {}".format(e))
        ################################################################
        return data
    
    def unlink(self):
        for record in self:
            prestashop_category_id = record.prestashop_category_id
            data = super(ExportProductCategoryPrestashop, record).unlink()
            ################################################################
            prestashop_crud = self.env['ir.config_parameter'].sudo().get_param('x_prestashop_crud')
            if int(prestashop_crud):
                self._cr.commit()
                try:
                    if prestashop_category_id:
                        self.categories_sincronize_delete(prestashop_category_id)
                except Exception as e:
                    _logger.info("Error al importar en prestashop {}".format(e))
            ################################################################
        return data

    def categories_sincronize(self, operation):
        if(self.id):
            self.ensure_one()
            prestashop_store_id = self.env['prestashop.store.details'].search([('id', '!=', False)])
            api_operation = "http://%s@%s/api/languages/?output_format=JSON&display=full" % (
                            prestashop_store_id and prestashop_store_id.prestashop_api_key,
                            prestashop_store_id and prestashop_store_id.prestashop_api_url)

            service_root = etree.Element("prestashop")
            request = etree.SubElement(service_root, "categories")
            name_tree =  etree.SubElement(request, "name")
            link_rewrite = etree.SubElement(request, "link_rewrite")

            response_status, languages_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(api_operation)
            languages = languages_data.get('languages')            

            if operation == 'PUT':
                etree.SubElement(request, "id").text ="%s"%(self.prestashop_category_id)

            if(response_status and len(languages) > 0):
                for language in languages:
                    lan_id = language.get('id')
                    etree.SubElement(name_tree, "language", id = "%s"%(lan_id)).text ="%s"%(self.name)
                    etree.SubElement(link_rewrite, "language", id = "%s"%(lan_id)).text ="%s"%(self.name.replace(" ", "-"))
            else:
                etree.SubElement(name_tree, "language", id = "0").text ="%s"%(self.name)
                etree.SubElement(link_rewrite, "language", id = "0").text ="%s"%(self.name.replace(" ", "-"))
            
            parent_id = self.parent_id and self.parent_id.prestashop_category_id
            if not parent_id:
                parent_id = 2
            etree.SubElement(request, "id_parent").text = "%s"%(int(parent_id))
            etree.SubElement(request, "date_add").text ="%s"%(self.create_date.date())
            etree.SubElement(request, "date_upd").text ="%s"%(self.write_date.date())
            etree.SubElement(request, "active").text = "1"

            etree.dump(request)
            
            data = "%s" % (prestashop_store_id.prestashop_api_key)
            encode_data = base64.b64encode(data.encode("utf-8"))
            authrization_data = "Basic %s" % (encode_data.decode("utf-8"))
            headers = {"Content-Type": "application/xml","Authorization": "%s" % authrization_data}
            url = "http://%s@%s/api/categories/?output_format=JSON&resource=categories" % (
                prestashop_store_id and prestashop_store_id.prestashop_api_key,
                prestashop_store_id and prestashop_store_id.prestashop_api_url)
            try:
                xml= etree.tostring(service_root)
                response_body = requests.request(operation, url=url, data=xml, headers=headers)
                if response_body.status_code in [200, 201]:
                    response_body = response_body.json()
                    self.write({
                        'prestashop_category_url': self.name,
                        'prestashop_parent_category_id': response_body.get('category').get('id_parent'),
                        'prestashop_category_id': response_body.get('category').get('id'),
                    }, sincronize=False)
                    _logger.info("Prestashop API Response Data : %s" % (response_body))
                    return True
                else:
                    _logger.info("Prestashop API Response Data : %s" % (response_body.text))
                    return False
            except Exception as e:
                _logger.info("Prestashop API Response Data : %s" % (e))
                return False, e
    
    def categories_sincronize_delete(self, id):
        if(id):
            prestashop_store_id = self.env['prestashop.store.details'].search([('id', '!=', False)])

            data = "%s" % (prestashop_store_id.prestashop_api_key)
            encode_data = base64.b64encode(data.encode("utf-8"))
            authrization_data = "Basic %s" % (encode_data.decode("utf-8"))
            headers = {"Content-Type": "application/xml","Authorization": "%s" % authrization_data}
            url = "http://%s@%s/api/categories/%s" % (
                prestashop_store_id and prestashop_store_id.prestashop_api_key,
                prestashop_store_id and prestashop_store_id.prestashop_api_url,
                id)
            try:
                response_body = requests.request('DELETE', url=url, headers=headers)
                if response_body.status_code in [200, 201]:
                    _logger.info("Prestashop API Response Data : Delete")
                    return True
                else:
                    _logger.info("Prestashop API Response Data : %s" % (response_body.text))
                    return False
            except Exception as e:
                _logger.info("Prestashop API Response Data : %s" % (e))
                return False, e