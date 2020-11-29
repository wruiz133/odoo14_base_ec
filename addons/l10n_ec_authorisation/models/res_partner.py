# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    authorisation_ids = fields.One2many(
        "account.authorisation",
        "partner_id",
        string="Autorizaciones"
        )

    def get_authorisation(self, type_document):
        map_type = {
            "out_invoice": "18",
            "in_invoice": "01",
            "out_refund": "04",
            "in_refund": "05",
            "liq_purchase": "03",
            "ret_in_invoice": "07",
        }
        code = map_type[type_document]
        for a in self.authorisation_ids:
            if a.active and a.type_id.code == code:
                return a
        return False
