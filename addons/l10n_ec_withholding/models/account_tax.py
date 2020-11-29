# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    retention_id = fields.Many2one(
        "account.retention",
        "Retención",
        index=True
    )

    def get_invoice(self, number):
        return self.env["account.move"].search([("number", "=", number)])

    @api.onchange("tax_id")
    def _onchange_tax(self):
        if not self.tax_id:
            return
        self.name = self.tax_id.description
        self.account_id = self.tax_id.account_id and self.tax_id.account_id.id
        self.base = self.retention_id.invoice_id.amount_untaxed
        self.amount = self.tax_id.compute_all(self.retention_id.invoice_id.amount_untaxed)["taxes"][0]["amount"]  # noqa
