# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Ecuadorian Accounting by Trescloud",
    "version": "3.3",
    "description": """ """,
    "author": "TRESCLOUD",
    "category": "Localization",
    "maintainer": "TRESCLOUD CIA. LTDA.",
    "website": "http://www.trescloud.com",
    "license": "OEEL-1",
    "depends": [
        "l10n_latam_invoice_document",
        "l10n_latam_base",
    ],   
    "data": [
        #Chart of Accounts
        "data/account_chart_template_data.xml",
        "data/account_group_template_data.xml",
        "data/account.account.template.csv",
        "data/account_chart_template_setup_accounts.xml",
        #Taxes
        "data/account_tax_group_data.xml",
        "data/account_tax_tag_data.xml",
        "data/account_tax_template_vat_data.xml",
        "data/account_tax_template_withhold_profit_data.xml",
        "data/account_tax_template_withhold_vat_data.xml",
        "data/account_fiscal_position_template.xml",
        "data/account_chart_template_configure_data.xml",
        "data/res_country.xml", #TODO move into Odoo core
        #Partners data
        "data/res_country_state_data.xml",
        "data/res_bank_data.xml",
        "data/l10n_latam_identification_type_data.xml",
        "data/res_partner_data.xml",
        #Other data
        "data/l10n_latam_document_type_data.xml",
        #Views
        "views/account_tax_view.xml",
        "views/l10n_latam_document_type_view.xml",
        "views/res_partner_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
