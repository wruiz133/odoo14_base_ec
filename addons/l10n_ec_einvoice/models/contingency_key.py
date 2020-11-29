# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CompanyContingencyKey(models.Model):
    _name = "res.company.contingency.key"
    _description = "Claves de Contingencia"
    _sql_constraints = [
        (
            "key_unique",
            "unique(key)",
            u"Clave de contingencia asignada debe ser única."
        )
    ]

    @api.model
    def _get_company(self):
        if self._context.get("company_id", False):
            return self._context.get("company_id")
        else:
            return self.env.user.company_id.id

    key = fields.Char(
        "Clave",
        size=37,
        required=True
    )
    used = fields.Boolean(
        "¿Utilizada?",
        readonly=True
    )
    company_id = fields.Many2one(
        "res.company",
        "Empresa",
        required=True,
        default=_get_company
    )

