{
    'name': 'pabs_sale_report',
    'category': 'sales',
    'summary': 'sale Report Customization',
    'version': '1.0',
    'description': """Customization of ticket module as per requirement.""",
    'depends': ['base', 'sale', 'account', 'account_accountant', 'pabs_account'],
    'data': [
        'data/report_paperformat.xml',
        'views/sale_report.xml',
        'views/sale_report_template.xml',
        'views/sale_report_template.xml',
        'views/sale_report_by_email.xml',
        'views/views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
