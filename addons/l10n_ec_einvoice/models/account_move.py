# -*- coding: utf-8 -*-

import itertools
import logging
import os
import time

from jinja2 import Environment, FileSystemLoader

from odoo import api, models
from odoo.exceptions import Warning as UserError

from . import utils
from ..xades.sri import DocumentXML
from ..xades.xades import Xades


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "account.edocument"]
    _logger = logging.getLogger("account.edocument")
    TEMPLATES = {
        "out_invoice": "out_invoice.xml",
        "out_refund": "out_refund.xml"
    }

    def _info_factura(self, invoice):
        """cuando llega aca ya debe exitir infofactura que esta
        en moduo edocument.py todos los datos estan en relacion
        al cliente y las sumas de los valores del detalle
        """

        def fix_date(date):
            d = time.strftime("%d/%m/%Y", time.strptime(str(date), "%Y-%m-%d"))
            return d

        company = invoice.company_id
        partner = invoice.partner_id
        infoFactura = {
            "fechaEmision": fix_date(invoice.invoice_date), #fecha convertida a dd/mm/yyyy
            "dirEstablecimiento": company.street2,
            "obligadoContabilidad": "SI",
            "tipoIdentificacionComprador": utils.tipoIdentificacion[partner.l10n_latam_identification_type_id.name],  # noqa
            "razonSocialComprador": partner.name,
            "identificacionComprador": partner.vat,
            "totalSinImpuestos": "%.2f" % (invoice.amount_untaxed), # monto neto
            "totalDescuento": "0.00",
            "propina": "0.00",
            "importeTotal": "{:.2f}".format(invoice.amount_pay), # monto con impuestos
            "moneda": "DOLAR",
            "formaPago": invoice.epayment_id.code, # codigo de la forma de pago
            "valorRetIva": "{:.2f}".format(invoice.taxed_ret_vatsrv+invoice.taxed_ret_vatb),  # noqa toma de renciones
            "valorRetRenta": "{:.2f}".format(invoice.amount_tax_ret_ir)
        }
        if company.company_registry: # carga el valor de si llena Sociedad, Contribuyente especial, etc
            infoFactura.update({"contribuyenteEspecial":
                                company.company_registry})
        else:
            raise UserError("No ha determinado si es contribuyente especial.")

        totalConImpuestos = [] # contiene la estructura arreglo que contiene diccionario de impuestos
        #for tax in invoice.tax_line_ids:
        for tax in invoice.line_ids.tax_ids:
           # print("//TAXFAC//invoice.tax_line_ids={0}".format(invoice.tax_line_ids))
            if tax.tax_group_id.l10n_ec_type in ["vat12", "vat14","zero_vat", "exempt_vat","ice"]:
                totalImpuesto = {
                    "codigo": utils.tabla17[tax.tax_group_id.l10n_ec_type],
                    "codigoPorcentaje": utils.tabla18[tax.percent_report],
                    #"baseImponible": "{:.2f}".format(tax.move_id.amount_untaxed),#"{:.2f}".format(tax.base),
                    "baseImponible": "{:.2f}".format(invoice.amount_untaxed),
                    #"tarifa": tax.percent_report,
                    "tarifa": tax.amount,
                    #"valor": "{:.2f}".format(tax.invoice_id.amount_tax)
                    "valor": "{:.2f}".format(invoice.amount_tax)
                    }
        totalConImpuestos.append(totalImpuesto)
        infoFactura.update({"totalConImpuestos": totalConImpuestos}) # agreega los impuestos a infofactura

        compensaciones = False
        comp = self.compute_compensaciones() # crea estructura de compensaciones y si exite add al infofactura
        if comp:
            compensaciones = True
            infoFactura.update({
                "compensaciones": compensaciones,
                "comp": comp
            })

        if self.move_type == "out_refund": # ssi nc en factura de ventas add la estructura necesaria a infofactura
            inv = self.search([("invoice_number", "=", self.origin)], limit=1)
            #inv_number = "{0}-{1}-{2}".format(inv.invoice_number[:3], inv.invoice_number[3:6], inv.invoice_number[9:15]) 
            inv_number = "{0}-{1}-{2}".format(self.origin[:3], self.origin[3:6], self.origin[6:15])
           # print("NUMBER={0}".form(inv_number))
           # print("FECHA={0}".format(inv.date_invoice))
            notacredito = {
                "codDocModificado": "01",#inv.auth_inv_id.type_id.code,
                "numDocModificado": inv_number,
                "motivo": self.name,
                "fechaEmisionDocSustento":fix_date(inv.invoice_date),
                "valorModificacion": self.amount_total
            }
            infoFactura.update(notacredito)
        return infoFactura

    def _detalles(self, invoice):
        """ hace un remplazo en el iterable special
         (encode remplaza ñes % *) usadas en campo descripcion
        construye cada linea del detalle recalculando los valores
        construye la estructura de impuestos para cada linea
        """
        def fix_chars(code):
            special = [
                [u"%", " "],
                [u"º", " "],
                [u"Ñ", "N"],
                [u"ñ", "n"]
            ]
            for f, r in special:
                code = code.replace(f, r)
            return code

        detalles = []
        for line in invoice.invoice_line_ids:
            codigoPrincipal = line.product_id and \
                line.product_id.default_code and \
                fix_chars(line.product_id.default_code) or "001"
            priced = line.price_unit * (1 - (line.discount or 0.00) / 100.0)
            discount = (line.price_unit - priced) * line.quantity
            detalle = {
                "codigoPrincipal": codigoPrincipal,
                "descripcion": fix_chars(line.name.strip()),
                "cantidad": "%.6f" % (line.quantity),
                "precioUnitario": "%.6f" % (line.price_unit),
                "descuento": "%.2f" % discount,
                "precioTotalSinImpuesto": "%.2f" % (line.price_subtotal)
            }
            impuestos = []
            #for tax_line in line.invoice_line_tax_ids:
            for tax_line in invoice.line_ids.tax_ids:
                aux=tax_line.amount/100
                if tax_line.tax_group_id.l10n_ec_type in ["vat12", "vat14", "zero_vat", "exempt_vat", "ice"]:
                #if tax_line.tax_group_id.code in ["vat", "vat0", "ice"]:
                    impuesto = {
                        # "codigo": utils.tabla17[tax_line.tax_group_id.code],
                        # "codigoPorcentaje": utils.tabla18[tax_line.percent_report],  # noqa
                        # "tarifa": tax_line.percent_report,
                        # "baseImponible": "{:.2f}".format(line.price_subtotal),
                        # "valor": "{:.2f}".format(line.price_subtotal * aux)
                        "codigo": utils.tabla17[tax_line.tax_group_id.l10n_ec_type],
                        "codigoPorcentaje": utils.tabla18[tax_line.percent_report],
                        "baseImponible": "{:.2f}".format(invoice.amount_untaxed),
                        "tarifa": tax_line.amount,
                        "valor": "{:.2f}".format(invoice.amount_tax)
                    }
                    impuestos.append(impuesto)
            detalle.update({"impuestos": impuestos})
            detalles.append(detalle) # cada linea detalle calculada valores e impuesstos
        return {"detalles": detalles}

    def _compute_discount(self, detalles):
        total = sum([float(det["descuento"]) for det in detalles["detalles"]])
        return {"totalDescuento": total}

    def render_document(self, invoice, access_key, emission_code):
        """"__file__ como parametro da el path de templates
         buscando desde donde se ejecuta el programa
        en este caso /mnt/extra-addons/l10n_ec_einvoice/models/templates
        usa ninja2 para pasarle parametros al template"""
        tmpl_path = os.path.join(os.path.dirname(__file__), "templates") # obtine la carpeta templates
        print("wr tmpl_path (path decodificado)--->  ",tmpl_path )
        env = Environment(loader=FileSystemLoader(tmpl_path)) # arma  el apuntador
        # print("wr Valor de env () ---->  ", env)
        einvoice_tmpl = env.get_template(self.TEMPLATES[self.move_type]) # obtiene el out_invoice.xml
        data = {}
        data.update(self._info_tributaria(invoice, access_key, emission_code)) #carga datos obligados en infotributaria
        data.update(self._info_factura(invoice)) # carga datos normados por sri para infofactra (tag del xsd)
        detalles = self._detalles(invoice) # detalles estructurales de lineas de factura con impuestos
        data.update(detalles) # carga detalles
        data.update(self._compute_discount(detalles)) # detalles con descuentos nfotributaria, infofactura, detalles
        einvoice = einvoice_tmpl.render(data) # aca carga el xml con los datos consignados en data (ver out_invoice.xml)
        return einvoice

    def render_authorized_einvoice(self, autorizacion):
        tmpl_path = os.path.join(os.path.dirname(__file__), "templates")
        env = Environment(loader=FileSystemLoader(tmpl_path))
        einvoice_tmpl = env.get_template("authorized_einvoice.xml")
        auth_xml = {
            "estado": autorizacion.estado,
            "numeroAutorizacion": autorizacion.numeroAutorizacion,
            "ambiente": autorizacion.ambiente,
            "fechaAutorizacion": str(autorizacion.fechaAutorizacion.strftime("%d/%m/%Y %H:%M:%S")),  # noqa
            "comprobante": autorizacion.comprobante
        }
        auth_invoice = einvoice_tmpl.render(auth_xml)
        return auth_invoice

    def action_generate_einvoice(self):
        """
        Metodo de generacion de factura electronica
        TODO: usar celery para enviar a cola de tareas
        la generacion de la factura y envio de email
        einvoice tiene el codigo reenderizado al formato xsd del sri
        """
        for obj in self:
            if obj.move_type not in ["out_invoice", "out_refund"]:
                continue
            #self.check_date(obj.date_invoice)
            #self.check_before_sent()
            access_key, emission_code = self._get_codes(name="account.move") # access_key validada y tipo emision
            einvoice = self.render_document(obj, access_key, emission_code) # xml segun sri (xsd)
            print("///////verifica wr einvoice/////////={0}".format(einvoice))
            #print("///////einvoice/////////=", einvoice)
            inv_xml = DocumentXML(einvoice, obj.move_type) # instancia clase de sri.py
          #  print("///////inv_xml/////////={0}".format(inv_xml))
            inv_xml.validate_xml() # parsea xml con xsd guardados en templates, docs
            """Guardar xml documentos generados"""
            path="%s"%(obj.company_id.bills_generated) # recupera path guardado en bills_generated
            nfile ="%s.xml"%(access_key) # crea nombre access_key.xml
            file = open(os.path.join(path, nfile), "w") # abre .../fee/facturas/generadas/access_kye.xml
            file.write(einvoice)  # escribe  xml generado
            file.close() 
                
            xades = Xades() # instancia la firma modulo xades clase Xades
            file_pk12 = obj.company_id.electronic_signature
            # lee path y pass de firma registrado en company
            password = obj.company_id.password_electronic_signature
            # pasa xml, path y pass
            # print("///////einvoice que entra a firmarse /////////={0}".format(einvoice))
            path_xml_document = path +'/'+nfile
            path_signed='%s' %(obj.company_id.bills_signed)
            signed_document = xades.sign(path_xml_document, nfile, path_signed, file_pk12, password) # ejecuta java -jar ...jar ....# ejecuta java -jar ...jar ....
            signed_document1 = str(signed_document, 'utf-8') # bytes a str wr
            print('lo que sale luego de firmarse  y se  espera autorizacion sri /////////////    ', signed_document)
            # print('En este formato se guarda  *****************>>>>  ', signed_document1)
            """Guardar xml firmado, path a firmadas, access_key.xml firmado"""
            nfile ='%s.xml'%(access_key)
            file = open(os.path.join(path_signed,nfile),"w")
            file.write(signed_document1)
            file.close()
            """Datos de ambiente si es off/on line, pruebas o produccion"""
            ambiente=obj.company_id.env_service
            modo=obj.company_id.is_offline
            #
            # print("ambiente={0}".format(ambiente))
            # print("modo={0}".format(modo))
            
            """Ambiente Pruebas, """
            if ambiente=="1" and modo:
                ok, errores = inv_xml.send_receipt(signed_document, obj.company_id.recepcion_pruebas_offline)
                if not ok:
                    raise UserError(errores)
            if ambiente=="1" and not modo:               
                ok, errores = inv_xml.send_receipt(signed_document, obj.company_id.recepcion_pruebas_online)
                if not ok:
                    raise UserError(errores)
            if ambiente=="1" and modo:
                auth, m = inv_xml.request_authorization(access_key, obj.company_id.autorizacion_pruebas_offline)
                #print("auth, m ={0}{1}".format(auth, m))
           
            if ambiente=="1" and not modo: 
                auth, m = inv_xml.request_authorization(access_key, obj.company_id.autorizacion_pruebas_online)       
            
            """Ambiente Produccion"""
            if ambiente=="2" and modo:
                ok, errores = inv_xml.send_receipt(signed_document, obj.company_id.recepcion_offline)
                if not ok:
                    raise UserError(errores)
            if ambiente=="2" and not modo:              
                ok, errores = inv_xml.send_receipt(signed_document, obj.company_id.recepcion_online)
                if not ok:
                    raise UserError(errores)
            if ambiente=="2" and modo:
                auth, m = inv_xml.request_authorization(access_key, obj.company_id.autorizacion_offline)  
            
            if ambiente=="2" and not modo:
                auth, m = inv_xml.request_authorization(access_key, obj.company_id.autorizacion_online)
               
                
            
            
            """ok, errores = inv_xml.send_receipt(signed_document, wsr)
            if not ok:
                raise UserError(errores)
            auth, m = inv_xml.request_authorization(access_key, wsa)"""
            if not auth: 
                msg = " ".join(list(itertools.chain(*m)))
                raise UserError(msg)
            auth_einvoice = self.render_authorized_einvoice(auth)
            self.update_document(auth, [access_key, emission_code])
            """Guardar xml autorizado"""
            path_authorized="%s" %(obj.company_id.bills_authorized)
            nfile ="%s.xml"%(access_key)
            file = open(os.path.join(path_authorized,nfile),"w")
            file.write(auth_einvoice)  
            file.close()

    def invoice_print(self):
        return self.env["report"].get_action(
            self,
            "l10n_ec_einvoice.report_einvoice"
        )

    def action_generate_eretention(self):
        for obj in self:
            if not obj.journal_id.auth_ret_id.is_electronic:
                return True
            obj.retention_id.action_generate_document()

    def action_retention_create(self):
        super().action_retention_create()
        for obj in self:
            if obj.move_type in ['in_invoice', 'liq_purchase']:
                self.action_generate_eretention()
