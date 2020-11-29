# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Retenciones para Ecuador",
    "version": "14.0.1.0.0",
    "category": "Generic Modules/Accounting",
    "license": "AGPL-3",
    "depends": [
        "account",
        "l10n_ec_authorisation",
        "l10n_ec_base",
    ],
    "author": "",
    "website": "",
    "data": [
        "security/ir.model.access.csv",
        "data/account.fiscal.position.csv",
        #"data/res_partner_data.xml",
        "report/report_account_move.xml",
        "report/reports.xml",
        "views/account_move_view.xml",
        "views/account_retention_line_view.xml",
        "views/account_retention_view.xml",
    ]
}
