# -*- coding: utf-8 -*-


{
    'name': 'Bahrain - Accounting',
    'author': 'ProAdvisory Business Solution',
    'category': 'Localization',
    'description': """
Kingdom of Bahrain accounting chart and localization.
=======================================================

    """,
    'depends': ['base', 'account','account_reports', 'pabs_account', 'purchase'],
    'data': [
             'data/l10n_ae_data.xml',
             'data/account_data.xml',
             'data/l10n_ae_chart_data.xml',
             #'data/chart_account.xml',
             'data/account.account.template.csv',
             'data/l10n_ae_chart_post_data.xml',
             'data/account_tax_report_data.xml',
             'data/account_tax_template_data.xml',
             'data/account_chart_template_data.xml',
             'views/report_invoice_templates.xml',

    ],
}
