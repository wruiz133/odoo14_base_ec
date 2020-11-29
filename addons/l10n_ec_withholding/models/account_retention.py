# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models

from odoo.exceptions import UserError, ValidationError
from . import utils


class AccountWithdrawing(models.Model):
    """ Implementacion de documento de retencion """

    _name = "account.retention"
    _description = "Withdrawing Documents"
    _order = "date DESC"
    _sql_constraints = [
        (
            "unique_number_type",
            "unique(name,type)",
            u"El número de retención es único."
        )
    ]

    @api.depends("tax_ids.amount")
    def _compute_total(self):
        for ret in self:
            ret.amount_total = sum(tax.amount for tax in ret.tax_ids)

    def _get_period(self):
        result = {}
        for obj in self:
            result[obj.id] = self.env["account.period"].find(obj.date)[0]
        return result

    def _get_in_type(self):
        context = self._context
        return context.get("in_type", "ret_out_invoice")

    def _default_type(self):
        context = self._context
        return context.get("type", "out_invoice")

    @api.model
    def _default_currency(self):
        company = self.env["res.company"]._company_default_get("account.move")
        return company.currency_id

    @api.model
    def _default_authorisation(self):
        if self.env.context.get("in_type") == "ret_in_invoice":
            company = self.env["res.company"]._company_default_get("account.move")
            auth_ret = company.partner_id.get_authorisation("ret_in_invoice")
            return auth_ret

    STATES_VALUE = {"draft": [("readonly", False)]}

    name = fields.Char(
        "Número", 
        size=64, 
        readonly=True, 
        states=STATES_VALUE,
        copy=False
    )
    internal_number = fields.Char(
        "Número Interno", 
        size=64, 
        readonly=True,
        copy=False)
    manual = fields.Boolean(
        "Numeración Manual", 
        readonly=True, 
        states=STATES_VALUE,
        default=True
    )
    auth_id = fields.Many2one(
        "account.authorisation",
        "Autorizacion",
        readonly=True, 
        states=STATES_VALUE,
        domain=[("in_type", "=", "interno")], 
        default=_default_authorisation
    )
    type = fields.Selection(
        related="invoice_id.move_type",
        string="Tipo Comprobante",
        readonly=True,
        store=True,
        default=_default_type
    )
    in_type = fields.Selection(
        [
            ("ret_in_invoice", u"Retención a Proveedor"),
            ("ret_out_invoice", u"Retención de Cliente"),
            ("ret_in_refund", u"Retención Nota de Credito Proveedor"),
            ("ret_out_refund", u"Retención Nota de Credito Cliente"),
            ("ret_liq_purchase", u"Retención de Liquidación en Compras"),
            ("ret_in_debit", u"Retención de Nota de Debito Proveedor"),
            ("ret_out_debit", u"Retención Nota de Debito Cliente"),
        ],
        string="Tipo",
        readonly=True,
        default=_get_in_type
    )
    date = fields.Date(
        "Fecha Emision",
        readonly=True,
        states={"draft": [("readonly", False)]},
        required=True
    )
    invoice_id = fields.Many2one(
        "account.move",
        string="Documento",
        required=False,
        readonly=True,
        states=STATES_VALUE,
        copy=False
        )
    tax_ids = fields.One2many(
        "account.retention.line",
        "retention_id",
        "Detalle de Impuestos",
        readonly=True,
        states=STATES_VALUE,
        copy=False
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Empresa",
        required=True,
        readonly=True,
        states=STATES_VALUE
        )
    move_ret_id = fields.Many2one(
        "account.move",
        string="Asiento Retención",
        readonly=True,
        copy=False
    )
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("done", "Validado"),
            ("cancel", "Anulado")
        ],
        readonly=True,
        string="Estado",
        default="draft"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=_default_currency
    )
    amount_total = fields.Monetary(
        compute="_compute_total",
        string="Total",
        store=True,
        readonly=True
    )
    to_cancel = fields.Boolean(
        string="Para anulación",
        readonly=True,
        states=STATES_VALUE
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        change_default=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env["res.company"]._company_default_get("account.move")  # noqa
        )
    
    @api.onchange("move_type")
    def onchange_invoice_id(self):
        for ret in self:
            domain = [
                ("state", "=", "open"),
                ("partner_id", "=", ret.partner_id), 
                ("retention_id", "=", False)
            ]
            if ret.in_type == "ret_out_invoice":
                domain.append(("move_type", "=", "out_invoice"))
            else:
                domain.append(("move_type", "=", "in_invoice"))
            return {"domain": {"invoice_id": domain}}

    @api.onchange("date")
    @api.constrains("date")
    def _check_date(self):
        if self.date and self.invoice_id:
            inv_date = datetime.strptime(str(self.invoice_id.date_invoice), "%Y-%m-%d")  # noqa
            ret_date = datetime.strptime(str(self.date), "%Y-%m-%d")  # noqa
            days = ret_date - inv_date
            #if days.days not in range(1, 6):
            if days.days > 6:
                raise ValidationError(utils.CODE_701)  # noqa

    @api.onchange("name")
    @api.constrains("name")
    def _onchange_name(self):
        length = {
            "in_invoice": 15,
            "liq_purchase": 15,
            "out_invoice": 15,
            "out_debit": 15,
            "in_debit": 15
        }
        if not self.name or not self.type:
            return
        if not len(self.name) == length[self.type] or not self.name.isdigit():
            raise UserError(
                u"Nro incorrecto. Debe ser de 15 dígitos. %s" % (self.name))
        if self.in_type == "ret_in_invoice":
            if not self.auth_id.is_valid_number(int(self.name[6:])):
                raise UserError("Nro no pertenece a la secuencia.")

    def unlink(self):
        for obj in self:
            if obj.state in ["done"]:
                raise UserError("No se permite borrar retenciones validadas.")
        res = super(AccountWithdrawing, self).unlink()
        return res

    @api.onchange("to_cancel")
    def onchange_tocancel(self):
        if self.to_cancel:
            company = self.env["res.company"]._company_default_get("account.move")  # noqa
            self.partner_id = company.partner_id.id

    @api.onchange("invoice_id")
    def onchange_invoice(self):
        if not self.invoice_id:
            return
        self.type = self.invoice_id.move_type

    def action_number(self, number):
        for wd in self:
            if wd.to_cancel:
                raise UserError("El documento fue marcado para anular.")

            sequence = wd.auth_id.sequence_id
            if self.type != "out_invoice" and not number:
                number = sequence.next_by_id()
            wd.write({"name": number})
        return True

    def action_validate(self, number=None):
        """
        @number: Número para usar en el documento
        """
        self.action_number(number)
        return self.write({"state": "done"})

    def button_validate(self):
        """
        Botón de validación de Retención que se usa cuando
        se creó una retención manual, esta se relacionará
        con la factura seleccionada.
        """
        for ret in self:
            if not ret.proyecto:
                raise UserError("No ha aplicado impuestos.")
            self.action_validate(self.name)
            if ret.manual:
                ret.invoice_id.write({"retention_id": ret.id})
                self.create_move()
        return True

    def create_move(self):
        """
        Generacion de asiento contable para aplicar como
        pago a factura relacionada
        """
        for ret in self:
            inv = ret.invoice_id
            move_data = {
                "journal_id": inv.journal_id.id,
                "ref": ret.name,
                "date": ret.date
            }
            total_counter = 0
            lines = []
            for line in ret.proyecto:
                if not line.manual:
                    continue
                lines.append((0, 0, {
                    "partner_id": ret.partner_id.id,
                    "account_id": line.account_id.id,
                    "name": ret.name,
                    "debit": abs(line.amount),
                    "credit": 0.00
                }))

                total_counter += abs(line.amount)

            lines.append((0, 0, {
                "partner_id": ret.partner_id.id,
                "account_id": inv.account_id.id,
                "name": ret.name,
                "debit": 0.00,
                "credit": total_counter
            }))
            move_data.update({"line_ids": lines})
            move = self.env["account.move"].create(move_data)
            acctype = self.type == "in_invoice" and "payable" or "receivable"
            inv_lines = inv.move_id.line_ids
            acc2rec = inv_lines.filtered(
                lambda l: l.account_id.internal_type == acctype
            )
            acc2rec += move.line_ids.filtered(
                lambda l: l.account_id.internal_type == acctype
            )
            acc2rec.auto_reconcile_lines()
            ret.write({"move_ret_id": move.id})
            move.post()
        return True

    def action_cancel(self):
        """
        Método para cambiar de estado a cancelado el documento
        """
        for ret in self:
            if ret.move_ret_id:
                self.env["account.move"].search(
                    [("id", "=", ret.move_ret_id.id)]
                ).unlink()
                self.write({"state": "cancel"})
            data = {"state": "cancel"}
            if ret.to_cancel:
                # FIXME
                if (
                        len(ret.name) == 9
                        and ret.auth_id.is_valid_number(int(ret.name))
                ):
                    number = (
                            ret.auth_id.serie_entidad
                            + ret.auth_id.serie_emision
                            + ret.name
                    )
                    data.update({"name": number})
                else:
                    raise UserError(utils.CODE702)
            self.proyecto.write({"invoice_id": False})
            self.write({"state": "cancel"})
        return True

    def action_draft(self):
        for ret in self:
            ret.state = "draft"
            return True

    def action_print(self):
        """ Método para imprimir comprobante contable """
        return self.env["report"].get_action(
            self.move_id,
            "l10n_ec_withholding.account_withholding"
        )

