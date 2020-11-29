# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class Company(models.Model):
    _inherit = "res.company"
    
    def _localization_use_documents(self):
        """ This method is to be inherited by localizations 
        and return True if localization use documents """
        self.ensure_one()
        return (
            True if self.country_id == self.env.ref("base.ec")
            else super()._localization_use_documents()
        )

    accountant_id = fields.Many2one(
        "res.partner",
        string="Contador"
    )
    sri_id = fields.Many2one(
        "res.partner",
        string="Servicio de Rentas Internas"
    )
    cedula_rl = fields.Char(
        string="Cédula Representante Legal",
        size=10
    )
