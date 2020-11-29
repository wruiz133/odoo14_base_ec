# -*- coding: utf-8 -*-

import os
from io import StringIO, BytesIO
import base64
import logging
import binascii

from lxml import etree
from lxml.etree import fromstring, DocumentInvalid

try:
   from suds.client import Client
except ImportError:
    logging.getLogger('xades.sri').info('Instalar libreria suds-jurko')

from ..models import utils
from .xades import CheckDigit


SCHEMAS= {
    'out_invoice': 'schemas/factura.xsd',
    'out_refund': 'schemas/nota_credito.xsd',
    'withdrawing': 'schemas/retencion.xsd',
    'delivery': 'schemas/guia_remision.xsd',
    'in_refund': 'schemas/nota_debito.xsd'
}


class DocumentXML(object):
    _schema = False
    document = False

    @classmethod
    def __init__(self, document, type='out_invoice'):
        """
        document: XML representation. Hace el parser xml xsd
        type: determinate schema
        """
        parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        self.document = fromstring(document.encode('utf-8'), parser=parser)
        self.type_document = type
        self._schema = SCHEMAS[self.type_document] # asocia xsd
        self.signed_document = False
        self.logger = logging.getLogger('xades.sri')

    @classmethod
    def validate_xml(self):
        """
        Validar esquema XML. Se imprime en formato 
        """
        self.logger.info('Validacion de esquema')
        self.logger.debug(etree.tostring(self.document, pretty_print=True))
        file_path = os.path.join(os.path.dirname(__file__), self._schema) # path schema
        schema_file = open(file_path) # abre comunicacion
        xmlschema_doc = etree.parse(schema_file)
        xmlschema = etree.XMLSchema(xmlschema_doc) # xsd schema
        try:
            xmlschema.assertValid(self.document) # parsea el xml
            return True
        except DocumentInvalid:
            return False

    @classmethod
    def send_receipt(self, document, web_service):
        """
        Metodo que envia el XML al WS
        """
        self.logger.info('Enviando documento para recepcion SRI')
        buf = StringIO()
        # buf = BytesIO()
        # print('xml firmado antes que se meta al buffer  >>>>>>   ', document, '  el tipo es >>> ', type(document))
        buf.write(str(document,"utf-8")) #aumenta str  utf-8 sino da error, se almacena
        # buffer_xml = str(base64.b64encode(buf.getvalue().encode("utf-8")), "utf-8")
        buffer_xml = str(base64.b64encode(buf.getvalue().encode()), "utf-8") # wr estaba encodestring
        print('Cuando buffer pasa b64encode  >>>>>   ', buffer_xml)
        #print('buffer tipo ...   ', type(buffer))
        # buffer_xml = str(base64.b64encode(buf.getvalue().encode("utf-8")), "utf-8")
        if not utils.check_service('prueba'):
            # TODO: implementar modo offline
            raise 'Error SRI'('Servicio SRI no disponible.')

        print("web_service apuntado desde company =   {0}   ".format(web_service))
        #client = Client(SriService.get_active_ws()[0])
        client = Client(web_service) # inatancia apuntando al ws del sri
        # print('procesado y antes de validar....   ', str(buffer_xml,'utf-8')
        # ejecuta metodo validarComprobante que viene en el ws sri
        result = client.service.validarComprobante(buffer_xml)
        print('fueera de validarcomprobante  result **>>>>>>  ', result)
       # self.logger.info('Estado de respuesta documento: %s' % result.estado)
        errores = []
        if result.estado == 'RECIBIDA':
                return True, errores
        else:
            for comp in result.comprobantes:
                for m in comp[1][0].mensajes:
                    rs = [m[1][0].tipo, m[1][0].mensaje]
                    rs.append(getattr(m[1][0], 'informacionAdicional', ''))
                    errores.append(' '.join(rs))
            self.logger.error(errores)
            return False, ', '.join(errores)

    def request_authorization(self, access_key, web_service_a):
        messages = []
        #client = Client(SriService.get_active_ws()[1])
        client = Client(web_service_a)
        result = client.service.autorizacionComprobante(access_key)
        self.logger.debug("Respuesta de autorizacionComprobante:SRI")
        self.logger.debug(result)
        autorizacion = result.autorizaciones[0][0]
        mensajes = autorizacion.mensajes and autorizacion.mensajes[0] or []
        self.logger.info('Estado de autorizacion %s' % autorizacion.estado)
        for m in mensajes:
            self.logger.error('{0} {1} {2}'.format(
                m.identificador, m.mensaje, m.tipo, m.informacionAdicional)
            )
            messages.append([m.identificador, m.mensaje,
                             m.tipo, m.informacionAdicional])
        if not autorizacion.estado == 'AUTORIZADO':
            return False, messages
        return autorizacion, messages


class SriService(object):

    __AMBIENTE_PRUEBA = '1'
    __AMBIENTE_PROD = '2'
    __ACTIVE_ENV = False
    # revisar el utils
    __WS_TEST_RECEIV = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'  # noqa
    __WS_TEST_AUTH = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'  # noqa
    __WS_RECEIV = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'  # noqa
    __WS_AUTH = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'  # noqa

    __WS_TESTING = (__WS_TEST_RECEIV, __WS_TEST_AUTH)
    __WS_PROD = (__WS_RECEIV, __WS_AUTH)

    _WSDL = {
        __AMBIENTE_PRUEBA: __WS_TESTING,
        __AMBIENTE_PROD: __WS_PROD
    }
    __WS_ACTIVE = __WS_TESTING

    @classmethod
    def set_active_env(self, env_service):
        if env_service == self.__AMBIENTE_PRUEBA:
            self.__ACTIVE_ENV = self.__AMBIENTE_PRUEBA
        else:
            self.__ACTIVE_ENV = self.__AMBIENTE_PROD
        self.__WS_ACTIVE = self._WSDL[self.__ACTIVE_ENV]

    @classmethod
    def get_active_env(self):
        return self.__ACTIVE_ENV

    @classmethod
    def get_env_test(self):
        return self.__AMBIENTE_PRUEBA

    @classmethod
    def get_env_prod(self):
        return self.__AMBIENTE_PROD

    @classmethod
    def get_ws_test(self):
        return self.__WS_TEST_RECEIV, self.__WS_TEST_AUTH

    @classmethod
    def get_ws_prod(self):
        return self.__WS_RECEIV, self.__WS_AUTH

    @classmethod
    def get_active_ws(self):
        return self.__WS_ACTIVE

    @classmethod
    def create_access_key(self, values):
        """ entra clave acceso en crudo, intercala el ambiente y obtiene el digito verificador
        values: tuple ([], [])
        """
        env = self.get_active_env() # obtiene ambiente ya configurado
        print('clave final val0 {0} env {1} values {2}   :  '.format(values[0], [env], values[1]))
        dato = ''.join(values[0] + [env] + values[1]) # intercala el ambiente en que se pide autorizacion
        modulo = CheckDigit.compute_mod11(dato) # aplica digito verificador mod 11
        access_key = ''.join([dato, str(modulo)]) # agrega digito verificador
        return access_key
