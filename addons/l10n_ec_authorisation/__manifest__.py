# -*- coding: utf-8 -*-

{
    "name": "Establecimientos y autorizaciones del SRI",
    "version": "14.0.1.0.0",
    "author": "",
    "category": "Localization",
    "license": "AGPL-3",
    "website": "",
    "data": [
        "data/account.ats.doc.csv",
        "data/account.ats.sustento.csv",
        "security/ir.model.access.csv",
        "views/account_move_view.xml",
        "views/account_journal_view.xml",
        "views/res_partner_view.xml",
        "views/authorisation_view.xml",
    ],
    "depends": [
        "l10n_ec_base",
        "account"
    ]
}
