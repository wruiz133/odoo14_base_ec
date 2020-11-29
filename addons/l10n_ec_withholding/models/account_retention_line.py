# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountRetentionLine(models.Model):
    _name = "account.retention.line"

    amount = fields.Float(string="Monto")
    sequence = fields.Integer(string="Secuencia")
    base = fields.Float(string="Base")
    group_id = fields.Many2one(
        "account.tax.group",
        string="Grupo"
    )
    tax_id = fields.Many2one(
        "account.tax",
        string="Impuesto"
    )
    tax_repartition_line_id = fields.Many2one("account.tax.repartition.line")
    retention_id = fields.Many2one(
        "account.retention",
        string="Retención"
    )
    num_document = fields.Char(string="Numero documento")
    fiscal_year = fields.Char(string="Periodo Fiscal")
    code = fields.Char(
        string="Codigo",
        related="tax_id.description",
        readonly=True
    )
    name = fields.Char(
        string="Nombre",
        related="tax_id.name",
        readonly=True
    )
    account_id = fields.Many2one(
        "account.account",
        string="Cuenta"
    )
