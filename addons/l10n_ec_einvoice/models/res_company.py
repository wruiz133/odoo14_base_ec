# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    electronic_signature = fields.Char(
        "Firma Electrónica",
        size=128,
    )
    password_electronic_signature = fields.Char(
        "Clave Firma Electrónica",
        size=255,
    )
    emission_code = fields.Selection(
        [
            ("1", "Normal"),
            ("2", "Indisponibilidad")
        ],
        string="Tipo de Emisión",
        required=True,
        default="1"
    )
    env_service = fields.Selection(
        [
            ("1", "Pruebas"),
            ("2", "Producción")
        ],
        string="Tipo de Ambiente",
        required=True,
        default="1"
    )
    contingency_key_ids = fields.One2many(
        "res.company.contingency.key",
        "company_id",
        "Claves de Contingencia",
        help="Claves de contingencia relacionadas con esta empresa.")
    bills_generated = fields.Char(
        "Facturas Generadas",
        size=128,
        required=True,
        help="Ubicación de carpeta que almacena XML de facturas generadas"
    )
    bills_signed = fields.Char(
        "Facturas Firmadas",
        size=128,
        required=True,
        help="Ubicación de carpeta que almacena XML de facturas firmadas"
    )
    bills_authorized = fields.Char(
        "Facturas Autorizadas",
        size=128,
        required=True,
        help="Ubicación de carpeta que almacena XML "
             "de facturas autorizadas por el SRI"
    )
    vouchers_generated = fields.Char(
        "Comprobantes de Retención Generados",
        size=128,
        required=True,
        help="Ubicación de carpeta que almacena XML "
             "de comprobantes generados"
    )
    vouchers_signed = fields.Char(
        "Comprobantes de Retención Firmados",
        size=128,
        required=True,
        help="Ubicación de carpeta que almacena "
             "XML de comprobantes firmados"
    )
    vouchers_authorized = fields.Char(
        "Comprobantes de Retención Autorizados",
        size=128,
        required=True,
        help="Ubicación de carpeta que almacena XML"
             " de comprobantes autorizados por el SRI"
    )
    credit_note_generated = fields.Char(
        "Notas de Crédito Generadas",
        size=128,
        required=True,
        help="Ubicación de carpeta que almacena "
             "XML de notas de crédito generadas"
    )
    credit_note_signed = fields.Char(
        "Notas de Crédito Firmadas",
        size=128,
        required=True,
        help="Ubicación de carpeta que almacena "
             "XML de notas de crédito firmadas"
    )
    credit_note_authorized = fields.Char(
        "Notas de Crédito Autorizadas",
        size=128,
        required=True,
        help="Ubicación de carpeta que almacena"
             " XML de notas de crédito autorizadas por el SRI"
    )
    is_offline = fields.Boolean(
        "Facturación Offline",
        default=lambda *a: False
    )
    recepcion_online = fields.Char("URL Recepción Online")
    autorizacion_online = fields.Char("URL Autorización Online")
    recepcion_offline = fields.Char("URL Recepción Offline")
    autorizacion_offline = fields.Char("URL Autorización Offline")
    recepcion_pruebas_online = fields.Char("URL Recepción pruebas Online")
    autorizacion_pruebas_online = fields.Char("URL Autorización pruebas Online")
    recepcion_pruebas_offline = fields.Char("URL Recepción pruebas Offline")
    autorizacion_pruebas_offline = fields.Char("URL Autorización pruebas Offline")
