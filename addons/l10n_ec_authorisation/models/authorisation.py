# -*- coding: utf-8 -*-
from datetime import datetime
import time

from odoo import api, fields, models
from odoo.exceptions import ValidationError, Warning as UserError


class AccountAtsDoc(models.Model):
    """Incorpora establecimientos y libreta de autorizaciones además
    de datos para documentos validos  para el ats y sustentos,
     se instalan en configuraciones contables.
    too se configuran los diaroos de ventas con la referencia
     a la autorizacion de ventas y nc y el de compras
    con referencia autorizar retenciones, las autorizaciones 
    para proveedores desde las facturas recibidas; para clientes desde
    el diario de ventas tanto para factura como para nc
    """
    _name = "account.ats.doc"
    _description = "Tipos Comprobantes Autorizados"

    code = fields.Char(
        string="Código",
        size=2,
        required=True
    )
    name = fields.Char(
        string="Tipo Comprobante",
        size=64,
        required=True
    )


class AccountAtsSustento(models.Model):
    _name = "account.ats.sustento"
    _description = "Sustento del Comprobante"
    _rec_name = "type"

    @api.depends("code", "type")
    def name_get(self):
        res = []
        for record in self:
            name = "%s - %s" % (record.code, record.type)
            res.append((record.id, name))
        return res

    code = fields.Char(
        "Código",
        size=2,
        required=True
    )
    type = fields.Char(
        "Tipo de Sustento",
        size=128,
        required=True
    )


class AccountAuthorisation(models.Model):
    _name = "account.authorisation"
    _order = "expiration_date desc"
    _description = ""
    _sql_constraints = [
        (
            "number_unique",
            "unique(partner_id,expiration_date,type_id)",
            u"La relación de autorización, serie entidad,"
            u" serie emisor y tipo, debe ser única."
         ),
        ]

    @api.depends("type_id", "num_start", "num_end")
    def name_get(self):
        res = []
        for record in self:
            name = u"%s (%s-%s)" % (
                record.type_id.code,
                record.num_start,
                record.num_end
            )
            res.append((record.id, name))
        return res

    @api.depends("expiration_date")
    def _compute_active(self):
        """
        Check the due_date to give the value active field
        """
        self.ensure_one()
        if not self.expiration_date:
            return
        
        now = datetime.strptime(str(time.strftime("%Y-%m-%d")), "%Y-%m-%d")
        due_date = datetime.strptime(str(self.expiration_date), "%Y-%m-%d")
        self.active = now <= due_date

    def _get_type(self):
        return self._context.get("type", "in_invoice")

    def _get_in_type(self):
        return self._context.get("in_type", "interno")#"externo")

    def _get_partner(self):
        partner = self.env.user.company_id.partner_id
        if self._context.get("partner_id"):
            partner = self._context.get("partner_id")
        return partner

    @api.model
    @api.returns("self", lambda value: value.id)
    def create(self, values):
        res = self.search(
            [
                ("partner_id", "=", values["partner_id"]),
                ("type_id", "=", values["type_id"]),
                ("serie_entidad", "=", values["serie_entidad"]),
                ("serie_emision", "=", values["serie_emision"]),
                ("active", "=", True)
            ]
        )
        if res:
            MSG = (
                    u"Ya existe una autorización activa para %s"
                    % self.type_id.name
            )
            raise ValidationError(MSG)

        partner_id = self.env.user.company_id.partner_id.id
        if values["partner_id"] == partner_id:
            typ = self.env["account.ats.doc"].browse(values["type_id"])
            name_type = "{0}_{1}".format(values["name"], values["type_id"])
            sequence_data = {
                "code": (
                        typ.code == "07"
                        and "account.retention"
                        or "account.invoice"
                ),
                "name": name_type,
                "padding": 9,
                }
            seq = self.env["ir.sequence"].create(sequence_data)
            values.update({"sequence_id": seq.id})
        return super().create(values)

    def unlink(self):
        inv = self.env["account.move"]
        res = inv.search([("auth_inv_id", "=", self.id)])
        if res:
            raise UserError(
                "Esta autorización esta relacionada a un documento."
            )
        return super().unlink()

    name = fields.Char(
        string="Num. de Autorización",
        size=128
    )
    serie_entidad = fields.Char(
        string="Serie Entidad",
        size=3,
        required=True
    )
    serie_emision = fields.Char(
        string="Serie Emision",
        size=3,
        required=True
    )
    num_start = fields.Integer(string="Desde")
    num_end = fields.Integer(string="Hasta")
    is_electronic = fields.Boolean(string="Documento Electrónico?")
    expiration_date = fields.Date(string="Fecha de Vencimiento")
    active = fields.Boolean(
        compute="_compute_active",
        string="Sec.Activo",
        store=True,
        default=True
    )
    in_type = fields.Selection(
        [
            ("interno", "Internas"),
            ("externo", "Externas")
        ],
        string="Tipo Interno",
        readonly=True,
        change_default=True,
        default=_get_in_type
    )
    type_id = fields.Many2one(
        "account.ats.doc",
        string="Tipo de Comprobante",
        required=True
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Empresa",
        required=True,
        default=_get_partner
    )
    sequence_id = fields.Many2one(
        "ir.sequence",
        "Secuencia",
        help="""Secuencia Alfanumerica para el documento,
             se debe registrar cuando pertenece a la compañia""",
        ondelete="cascade"
    )

    def is_valid_number(self, number):
        """
        Metodo que verifica si @number esta en el rango
        de [@num_start,@num_end]
        """
        self.ensure_one()
        if not self.is_electronic:
            if self.num_start <= number <= self.num_end:
                return True
        return False


