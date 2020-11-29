# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 LS
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name' : 'Invoice-Retention Email',
    'version' : '0.1.0',
    'author' : 'LS',
    'category': 'Localization',
    #'complexity': 'normal',
    'website': 'http://www.leadsolutions.ec',
    'data': [
        'view/account_invoice_email_view.xml',
        'view/cr_action_data.xml',
        ],
    'depends' : ['base_setup','l10n_ec_einvoice','l10n_ec_withholding','l10n_ec_refund','mail',],
    'js': [
    ],
    'qweb': [
    ],
    'css': [
    ],
    'installable': True,
    'auto_install': False,  
}              

