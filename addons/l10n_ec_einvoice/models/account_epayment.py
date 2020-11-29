# -*- coding: utf-8 -*-


from odoo import api, fields, models


class AccountEpayment(models.Model):
    _name = "account.epayment"

    code = fields.Char(string="Código")
    name = fields.Char(string="Forma de Pago")
