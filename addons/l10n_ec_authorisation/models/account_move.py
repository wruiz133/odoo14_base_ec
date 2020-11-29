# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError, Warning as UserError


class AccountMove(models.Model):
    _inherit = "account.move"
    _sql_constraints = [
        (
            "unique_invoice_number",
            "unique(ref,move_type,partner_id,state)",
            u"El número de factura es único."
        )
    ]

    _DOCUMENTOS_EMISION = ["out_invoice", "liq_purchase", "out_refund"]

    # @api.onchange("journal_id", "auth_inv_id")
    # def _onchange_journal_id(self):
    #     super()._onchange_journal_id()
    #     if self.journal_id and self.type in self._DOCUMENTOS_EMISION:
    #         if self.type == "out_invoice":
    #             self.auth_inv_id = self.journal_id.auth_out_invoice_id
    #         elif self.type == "out_refund":
    #             self.auth_inv_id = self.journal_id.auth_out_refund_id
    #         self.auth_number = not self.auth_inv_id.is_electronic and self.auth_inv_id.name  # noqa
    #         number = "{0}".format(
    #             str(self.auth_inv_id.sequence_id.number_next_actual).zfill(9)
    #         )
    #         self.ref = number


    invoice_number = fields.Char(
        compute="_compute_invoice_number",
        string="Nro. Documento",
        store=True,
        readonly=True,
    )
    internal_inv_number = fields.Char(string="Numero Interno")
    auth_inv_id = fields.Many2one(
        "account.authorisation",
        string="Establecimiento",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Autorizacion para documento",
        copy=False
    )
    auth_number = fields.Char(
        string="Autorización",
        size=49
    )
    sustento_id = fields.Many2one(
        "account.ats.sustento",
        string="Sustento del Comprobante"
    )

    @api.onchange("partner_id", "company_id")
    def _onchange_partner_id(self):
        """
        Redefinicion de metodo para obtener:
        - numero de autorización
        - numero de documento
        El campo auth_inv_id representa la autorizacion para
        emitir el documento.
        """
        super()._onchange_partner_id()
        self.ensure_one()
        if self.move_type not in self._DOCUMENTOS_EMISION:
            self.auth_inv_id = self.partner_id.get_authorisation(
                self.move_type
            )

    @api.depends("state", "ref")
    def _compute_invoice_number(self):
        """
        Calcula el número de factura según el
        establecimiento seleccionado
        """
        self.ensure_one()
        #self.ref = self.l10n_latam_document_number
        if self.ref:
            self.invoice_number = "{0}{1}{2}".format(
                self.auth_inv_id.serie_entidad,
                self.auth_inv_id.serie_emision,
                #self.l10n_latam_document_number
                self.ref
            )
        else:
            self.invoice_number = "*"

    @api.onchange("auth_inv_id")
    def _onchange_auth(self):
        if self.auth_inv_id and not self.auth_inv_id.is_electronic:
            self.auth_number = self.auth_inv_id.name

    @api.constrains("auth_number")
    def check_ref(self):
        """
        Metodo que verifica la longitud de la autorizacion
        10: documento fisico
        35: factura electronica modo online
        49: factura electronica modo offline
        """
        if self.move_type not in ["in_invoice", "liq_purchase"]:
            return
        if self.auth_number and len(self.auth_number) not in [10, 35, 49]:
            raise UserError(
                u"Debe ingresar 10, 35 o 49 dígitos según el documento."
            )

    def action_number(self):
        # TODO: ver donde incluir el metodo de numeracion
        self.ensure_one()
        if self.move_type not in ["out_invoice", "liq_purchase", "out_refund"]:
            return
        number = self.internal_inv_number
        if not self.auth_inv_id:
            self._onchange_partner_id()
        if not number:
            sequence = self.auth_inv_id.sequence_id
            number = sequence.next_by_id()
        self.write({"ref": number, "internal_inv_number": number})

    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open,
        # so we remove those already open
        # redefined for numbering document
        to_open_invoices = self.filtered(lambda inv: inv.state != "open")
        if to_open_invoices.filtered(lambda inv: inv.state not in ["proforma2", "draft"]):  # noqa
            raise UserError(_("Invoice must be in draft or Pro-forma state in order to validate it."))  # noqa
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        to_open_invoices.action_number()
        return to_open_invoices.invoice_validate()
