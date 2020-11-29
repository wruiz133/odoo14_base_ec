# -*- coding: utf-8 -*-
# © <2018> <LS>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import  api, models
from odoo.exceptions import ValidationError

import base64



class account_retention(models.Model):
    _name = 'account.retention'
    _inherit = ['account.retention', 'mail.thread']

    @api.multi
    def action_cr_sent(self):

        for retention in self:
            email = retention.partner_id.email
            print("email = {0}".format(email ))
            if not email:
                raise ValidationError(u'%s No tiene configurada direccion de correo' % retention.partner_id.name)
                continue

        obj = self[0]
        name = '%s%s.xml'%(self.company_id.vouchers_authorized, obj.clave_acceso)
        print("name={0}".format(name))
        cadena = open(name, mode='rb').read()
        email_template_obj = self.env.get('mail.template')
        attachment_id = self.env.get('ir.attachment').create(
             {'name':'%s.xml'%(obj.clave_acceso),'datas': base64.b64encode(cadena),
             'datas_fname':'%s.xml'%(obj.clave_acceso),'res_model': self._name,'res_id':obj.id,'type':'binary'})

        self.ensure_one()
        template = self.env.ref('account_invoice_email.email_template_edi_cr',False)
        print("template={0}".format(template.id))
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        # email_template_obj.write(template.id, {'attachment_ids': [(6, 0, [attachment_id.id])]})

        ctx = dict(
            default_model='account.retention',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            #mark_invoice_as_sent=True,
            #custom_layout="account_invoice_email.email_template_edi_cr"
        )


        return {
            'name':'Compose Email',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

account_retention()

  
