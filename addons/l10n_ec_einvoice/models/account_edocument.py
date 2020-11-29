# -*- coding: utf-8 -*-

import base64
from io import StringIO
from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import Warning as UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


from . import utils
from ..xades.sri import SriService


class AccountEdocument(models.AbstractModel):
    _name = "account.edocument"
    _FIELDS = {
        "account.move": "name",
        "account.retention": "name"
    }
    SriServiceObj = SriService()

    clave_acceso = fields.Char(
        string="Clave de Acceso",
        size=49,
        readonly=True
    )
    numero_autorizacion = fields.Char(
        string="Número de Autorización",
        size=49,
        readonly=True
    )
    estado_autorizacion = fields.Char(
        string="Estado de Autorización",
        size=64,
        readonly=True
    )
    fecha_autorizacion = fields.Datetime(
        string="Fecha Autorización",
        readonly=True
    )
    ambiente = fields.Char(
        string="Ambiente",
        size=64,
        readonly=True
    )
    autorizado_sri = fields.Boolean(
        string="¿Autorizado SRI?",
        readonly=True
    )
    security_code = fields.Char(
        string="Código de Seguridad",
        size=8,
        readonly=True
    )
    emission_code = fields.Char(
        string="Tipo de Emisión",
        size=1,
        readonly=True
    )
    epayment_id = fields.Many2one(
        "account.epayment",
        string="Forma de Pago"
    )
    sent = fields.Boolean(string="Enviado?")

    def get_auth(self, document):
        partner = document.company_id.partner_id
        if document._name == "account.move":
            return document.auth_inv_id
        elif document._name == "account.retention":
            return partner.get_authorisation("ret_in_invoice")

    def get_secuencial(self):
        print('wr self._FIELDS[self._name] {}'.format(getattr(self, self._FIELDS[self._name])[6:]))
        return getattr(self, self._FIELDS[self._name])[6:]

    def _info_tributaria(self, document, access_key, emission_code):
        """entra factura, clave acceso, tipo emision; y
         arma la estructura de la cabecera infotributaria
         (desde el modulo einvoice.py se hereda factura y
          documento nasi usa los metodos indistintamente)
        """
        company = document.company_id
        auth = self.get_auth(document)
        infoTributaria = {
            "ambiente": self.env.user.company_id.env_service,
            "tipoEmision": emission_code,
            "razonSocial": company.name,
            "nombreComercial": company.name,
            "ruc": company.partner_id.vat,
            "claveAcceso":  access_key,
            "codDoc": utils.tipoDocumento[auth.type_id.code],
            "estab": auth.serie_entidad,
            "ptoEmi": auth.serie_emision,
            #"secuencial": self.get_secuencial(),
            "secuencial": self.env['ir.sequence'].next_by_code('edocuments.code'),
            "dirMatriz": company.street
        }
        return infoTributaria

    def get_code(self):
        """ Obtiene el siguiente secuencial"""
        code = self.env["ir.sequence"].next_by_code("edocuments.code")
        return code

    def get_access_key(self, name):
        if name == "account.move":
            doc = self.move_type
            ld = str(self.invoice_date).split("-")
            numero = getattr(self, "invoice_number")
            codigo_numero = self.get_code()
            # cod del tipo de dcto
            vals = {
                "out_invoice": "01",
                "out_refund": "04",
                "in_refund": "05",
                "liq_purchase": "03"
              }
            a = vals.get(doc)
        elif name == "account.retention":
            doc = self.in_type
            ld = self.date.split("-")
            numero = (
                    self.auth_id.serie_entidad
                    + self.auth_id.serie_emision
                    + getattr(self, "name")
            )
            codigo_numero = self.get_code()
            if doc == "ret_in_invoice": a = "07"
            
        ld.reverse()
        fecha = "".join(ld)
        tcomp = utils.tipoDocumento[a]
        #ruc = self.company_id.partner_id.identifier
        ruc = self.company_id.partner_id.vat
        tipo_emision = self.company_id.emission_code
        
        # crea la estructura (tuple de arreglos) de clave de acceso
        access_key = (
            [fecha, tcomp, ruc],
            [numero, codigo_numero, tipo_emision]
            )
        return access_key

    def _get_codes(self, name="account.move"):
        ak_temp = self.get_access_key(name)
        self.SriServiceObj.set_active_env(self.env.user.company_id.env_service)
        access_key = self.SriServiceObj.create_access_key(ak_temp)
        print('wr access_key verificado  {}'.format(access_key))
        emission_code = self.company_id.emission_code
        return access_key, emission_code

    def check_before_sent(self):
        """
        """
        MESSAGE_SEQUENCIAL = " ".join([
            u"Los comprobantes electrónicos deberán ser",
            u"enviados al SRI para su autorización en orden cronológico",
            "y secuencial. Por favor enviar primero el",
            " comprobante inmediatamente anterior."])
        FIELD = {
            "account.invoice": "invoice_number",
            "account.retention": "name"
        }
        number = getattr(self, FIELD[self._name])
        sql = " ".join([
            "SELECT autorizado_sri, %s FROM %s" % (FIELD[self._name], self._table),  # noqa
            "WHERE state='open' AND %s < '%s'" % (FIELD[self._name], number),  # noqa
            self._name == "account.invoice" and "AND type = 'out_invoice'" or "",  # noqa
            "ORDER BY %s DESC LIMIT 1" % FIELD[self._name]
        ])
        self.env.cr.execute(sql)
        res = self.env.cr.fetchone()
        if not res:
            return True
        auth, number = res
        if auth is None and number:
            raise UserError(MESSAGE_SEQUENCIAL)
        return True

    def check_date(self, date_invoice):
        """
        Validar que el envío del comprobante electrónico
        se realice dentro de las 24 horas posteriores a su emisión
        """
        LIMIT_TO_SEND = 5
        MESSAGE_TIME_LIMIT = u" ".join([
            u"Los comprobantes electrónicos deben",
            u"enviarse con máximo 24h desde su emisión."]
        )
        dt = datetime.strptime(str(date_invoice), "%Y-%m-%d")
        days = (datetime.now() - dt).days
        if days > LIMIT_TO_SEND:
            raise UserError(MESSAGE_TIME_LIMIT)

    def update_document(self, auth, codes):
        fecha = auth.fechaAutorizacion.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.write({
            "numero_autorizacion": auth.numeroAutorizacion,
            "estado_autorizacion": auth.estado,
            "ambiente": auth.ambiente,
            "fecha_autorizacion": fecha,
            "autorizado_sri": True,
            "clave_acceso": codes[0],
            "emission_code": codes[1]
        })

    def add_attachment(self, xml_element):
        self.ensure_one()
        buf = StringIO.StringIO()
        buf.write(xml_element.encode("utf-8"))
        document = base64.encodestring(buf.getvalue())
        buf.close()
        attach = self.env["ir.attachment"].create(
            {
                "name": "{0}.xml".format(self.clave_acceso),
                "datas": document,
                "datas_fname":  "{0}.xml".format(self.clave_acceso),
                "res_model": self._name,
                "res_id": self.id,
                "type": "binary"
            },
        )
        return attach

    def send_document(self, attachments=None, tmpl=False):
        self.ensure_one()
        self._logger.info("Enviando documento electronico por correo")
        tmpl = self.env.ref(tmpl)
        tmpl.send_mail(
            self.id,
            email_values={"attachment_ids": attachments}
        )
        self.sent = True
        return True

    def render_document(self, document, access_key, emission_code):
        pass
