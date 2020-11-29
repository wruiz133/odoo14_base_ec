# -*- coding: utf-8 -*-

import base64
import os
import subprocess
import logging


class CheckDigit(object):

    # Definicion modulo 11
    _MODULO_11 = {
        'BASE': 11,
        'FACTOR': 2,
        'RETORNO11': 0,
        'RETORNO10': 1,
        'PESO': 2,
        'MAX_WEIGHT': 7
    }

    @classmethod
    def _eval_mod11(self, modulo):
        if modulo == self._MODULO_11['BASE']:
            return self._MODULO_11['RETORNO11']
        elif modulo == self._MODULO_11['BASE'] - 1:
            return self._MODULO_11['RETORNO10']
        else:
            return modulo

    @classmethod
    def compute_mod11(self, dato):
        """
        Calculo mod 11
        return int
        """
        total = 0
        weight = self._MODULO_11['PESO']

        for item in reversed(dato):
            total += int(item) * weight
            weight += 1
            if weight > self._MODULO_11['MAX_WEIGHT']:
                weight = self._MODULO_11['PESO']
        mod = 11 - total % self._MODULO_11['BASE']

        mod = self._eval_mod11(mod)
        return mod


class Xades(object):

    def sign(self, xml_document, file_pk12, password):
        """
        Metodo que aplica la firma digital al XML
        TODO: Revisar return
        se codifica xml, command lanza java -jar pathjar xmlcodificado file_pk12 password
        ejecuta con subprocess.check_output
        """
        xml_str = xml_document.encode('utf-8')
        JAR_PATH = 'firma/firmaXadesBes.jar'
        JAVA_CMD = 'java'
        firma_path = os.path.join(os.path.dirname(__file__), JAR_PATH)
        # path al .jar
        # print('ya codificada  ', base64.b64encode(bytes(file_pk12, 'utf-8')))
        print('WR firmapath   ', firma_path)
        command = [
            JAVA_CMD,
            '-XX:MaxHeapSize=512m',
            '-jar',
            firma_path,
            xml_str,
            base64.b64encode(file_pk12.encode()),
            base64.b64encode(password.encode())
        ]
        # prueba la ejecucion del comando
        print('WR  Comando para el ja:  ', command)
        try:
            logging.info('Probando comando de firma digital')
            subprocess.check_output(command)
        except subprocess.CalledProcessError as e:
            returncode = e.returncode
            output = e.output
            logging.error('Llamada a proceso JAVA codigo: %s' % returncode)
            logging.error('Error: %s' % output)
        # abre el subproceso para ser ejecutado en segundo plano subprocess.Popen
        p = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        # ejecuta el comando  y comunica resultado a la pantalla p.communicate()[0].decode('utf-8')
        res = p.communicate()
        return res[0]
