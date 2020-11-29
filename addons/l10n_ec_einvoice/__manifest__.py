# -*- coding: utf-8 -*-
{
    "name": "Electronic Documents for Ecuador",
    "version": "14.0.1.0.0",
    "author": "",
    "category": "Localization",
    "license": "AGPL-3",
    "complexity": "normal",
    "data": [
        "security/ir.model.access.csv",
        "data/account.epayment.csv",
        "data/sequence.xml",
        "edi/einvoice_edi.xml",
        "views/account_epayment_view.xml",
        "views/account_move_view.xml",
        "views/account_retention_view.xml",
        "views/contingency_key_view.xml",
        "views/res_company_view.xml",
        "report/report_einvoice.xml",
        "report/report_eretention.xml",
        #"report/edocument_layouts.xml",
    ],
    "depends": ["l10n_ec_withholding"]
}
