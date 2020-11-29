# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    person_type = fields.Selection(
        compute="_compute_person_type",
        selection=[
            ("6", "Persona Natural"),
            ("9", "Persona Jurídica"),
            ("0", "Otro")
        ],
        string="Persona",
        store=True
    )

    # def validate_from_sri(self):
    #     """
    #     TODO
    #     """
    #     SRI_LINK = "https://declaraciones.sri.gob.ec/facturacion-internet/consultas/publico/ruc-datos1.jspa"  # noqa
    #     texto = '0103893954'  # noqa

    def check_vat_ec(self, vat):
        try:
            from stdnum.util import clean
            from stdnum.ec import ci, ruc
        except ImportError:
            return True

        if self.l10n_latam_identification_type_id.is_vat:
            vat = clean(vat, " -.").upper().strip()
            if self.l10n_latam_identification_type_id.name == "Ced":
                return ci.is_valid(vat)
            elif (
                    self.l10n_latam_identification_type_id.name == "RUC"
                    and vat != "9999999999999"
            ):
                return ruc.is_valid(vat)
        return True

    @api.depends("vat")
    def _compute_person_type(self):
        """179.. ruc para empresas, 170... 
        ruc/cedula pnatural"""
        
        for rec in self:
            if not rec.vat:
                rec.person_type = "0"
            elif int(rec.vat[2]) <= 6:
                rec.person_type = "6"
            elif int(rec.vat[2]) in [6, 9]:
                rec.person_type = "9"
            else:
                rec.person_type = "0"

    def _get_complete_address(self):
        self.ensure_one()
        partner_id = self
        address = ""
        if partner_id.street:
            address += partner_id.street + ", "
        if partner_id.street2:
            address += partner_id.street2 + ", "
        if partner_id.city:
            address += partner_id.city + ", "
        if partner_id.state_id:
            address += partner_id.state_id.name + ", "
        if partner_id.zip:
            address += "(" + partner_id.zip + ") "
        if partner_id.country_id:
            address += partner_id.country_id.name
        return address
