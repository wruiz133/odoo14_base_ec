# -*- coding: utf-8 -*-

import os
import time
import logging
import itertools

from jinja2 import Environment, FileSystemLoader

from odoo import api, fields, models
from odoo.exceptions import Warning as UserError

from . import utils
from ..xades.sri import DocumentXML
from ..xades.xades import Xades


class AccountWithdrawing(models.Model):
    _name = "account.retention"
    _inherit = [
        "account.retention",
        "account.edocument",
        "mail.thread",
        "mail.activity.mixin"
    ]
    _logger = logging.getLogger(_name)

    sri_sent = fields.Boolean('Enviado', default=False)
    # sri_errors = fields.One2many('sri.error', 'retencion_id',
    #                              string='Errores SRI')
    def get_secuencial(self):
        return getattr(self, "name")#[6:15]

    def _info_withdrawing(self, withdrawing):
        """
        """
        # generar infoTributaria
        company = withdrawing.company_id
        partner = withdrawing.invoice_id.partner_id
        infoCompRetencion = {
            "fechaEmision": time.strftime("%d/%m/%Y", time.strptime(str(withdrawing.date), "%Y-%m-%d")),  # noqa
            "dirEstablecimiento": company.street,
            "obligadoContabilidad": "SI",
            "tipoIdentificacionSujetoRetenido": utils.tipoIdentificacion[partner.type_identifier],  # noqa
            "razonSocialSujetoRetenido": partner.name,
            "identificacionSujetoRetenido": partner.identifier,
            "periodoFiscal": withdrawing.invoice_id.date_invoice[5:7]+"/"+ withdrawing.invoice_id.date_invoice[0:4]#withdrawing.period_id.name,
            }
        if company.company_registry:
            infoCompRetencion.update({"contribuyenteEspecial": company.company_registry})  # noqa
        return infoCompRetencion

    def _impuestos(self, retention):
        """
        """
        def get_codigo_retencion(linea):
            if linea.tax_id.tax_group_id.code in ["ret_vat_b", "ret_vat_srv"]:
                return utils.tabla21[linea.tax_id.percent_report]
            else:
                code = linea.code or linea.description
                return code

        impuestos = []
        for line in retention.tax_ids:
            impuesto = {
                "codigo": utils.tabla20[line.tax_id.tax_group_id.code],#utils.tabla20[line.tax_group],
                "codigoRetencion": get_codigo_retencion(line),
                "baseImponible": "%.2f" % (line.base),
                "porcentajeRetener": str(line.tax_id.percent_report),
                "valorRetenido": "%.2f" % (abs(line.amount)),
                "codDocSustento": retention.invoice_id.auth_inv_id.type_id.code,#retention.invoice_id.sustento_id.code,
                "numDocSustento": retention.invoice_id.invoice_number,#line.num_document,
                "fechaEmisionDocSustento": time.strftime("%d/%m/%Y", time.strptime(str(retention.invoice_id.date_invoice), "%Y-%m-%d"))  # noqa
            }
            impuestos.append(impuesto)
        return {"impuestos": impuestos}

    def render_document(self, document, access_key, emission_code):
        tmpl_path = os.path.join(os.path.dirname(__file__), "templates")
        env = Environment(loader=FileSystemLoader(tmpl_path))
        ewithdrawing_tmpl = env.get_template("ewithdrawing.xml")
        data = {}
        data.update(self._info_tributaria(document, access_key, emission_code))
        data.update(self._info_withdrawing(document))
        data.update(self._impuestos(document))
        edocument = ewithdrawing_tmpl.render(data)
        self._logger.debug(edocument)
        return edocument

    def render_authorized_document(self, autorizacion):
        tmpl_path = os.path.join(os.path.dirname(__file__), "templates")
        env = Environment(loader=FileSystemLoader(tmpl_path))
        edocument_tmpl = env.get_template("authorized_withdrawing.xml")
        auth_xml = {
            "estado": autorizacion.estado,
            "numeroAutorizacion": autorizacion.numeroAutorizacion,
            "ambiente": autorizacion.ambiente,
            "fechaAutorizacion": str(autorizacion.fechaAutorizacion.strftime("%d/%m/%Y %H:%M:%S")),  # noqa
            "comprobante": autorizacion.comprobante
        }
        auth_withdrawing = edocument_tmpl.render(auth_xml)
        return auth_withdrawing

    def action_generate_document(self):
        """
        """
        for obj in self:
            self.check_date(obj.date)
            self.check_before_sent()
            access_key, emission_code = self._get_codes("account.retention")
            ewithdrawing = self.render_document(obj, access_key, emission_code)
            print(" /////ewithdrawing /////={0}".format( ewithdrawing ))
            self._logger.debug(ewithdrawing)
            inv_xml = DocumentXML(ewithdrawing, "withdrawing")
            inv_xml.validate_xml()
            
            """Guardar xml documentos generados"""
            path="%s" %(obj.company_id.vouchers_generated)
            nfile="%s.xml"%(access_key)
            file = open(os.path.join(path,nfile),"w")
            file.write(ewithdrawing)  
            file.close()
            
            xades = Xades()
            file_pk12 = obj.company_id.electronic_signature
            password = obj.company_id.password_electronic_signature
            signed_document = xades.sign(ewithdrawing, file_pk12, password)
            
            """Guardar xml firmado"""
            path_signed="%s" %(obj.company_id.vouchers_signed)
            nfile="%s.xml"%(access_key)
            file = open(os.path.join(path_signed,nfile),"w")
            file.write(signed_document)  
            file.close()
            
            """Datos de ambiente"""
            ambiente=obj.company_id.env_service
            modo=obj.company_id.is_offline
            
            print("ambiente-cr={0}".format(ambiente))
            print("modo-cr={0}".format(modo))
            
            """Ambiente Pruebas"""
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
            
            
            if not auth:
                msg = " ".join(list(itertools.chain(*m)))
                raise UserError(msg)
            auth_document = self.render_authorized_document(auth)
            self.update_document(auth, [access_key, emission_code])
            
            """Guardar xml autorizado"""
            path_authorized="%s" %(obj.company_id.vouchers_authorized)
            nfile="%s.xml"%(access_key)
            file = open(os.path.join(path_authorized,nfile),"w")
            file.write(auth_document)  
            file.close()
            
            attach = self.add_attachment(auth_document, auth)
            """self.send_document(
                attachments=[a.id for a in attach],
                tmpl="l10n_ec_einvoice.email_template_eretention"
            )"""
            return True

    def retention_print(self):
        return self.env["report"].get_action(
            self,
            "l10n_ec_einvoice.report_eretention"
        )


