# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    auth_out_invoice_id = fields.Many2one(
        "account.authorisation",
        string="Secuencia Facturas"
    )
    auth_out_refund_id = fields.Many2one(
        "account.authorisation",
        string="Secuencia Notas de Credito"
    )
    auth_retention_id = fields.Many2one(
        "account.authorisation",
        string="Para Retenciones"
    )

