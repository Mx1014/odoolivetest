{
    'name': 'pabs_service',
    'category': 'repsir',
    'summary': 'Service Report Customization',
    'version': '1.0',
    'description': """Customization of ticket module as per requirement.""",
    'depends': ['base', 'sale', 'account', 'account_accountant', 'sale_management', 'stock', 'sale_stock', 'pabs_sale',
                'pabs_repair'],
    'data': [
        'data/report_paperformat.xml',
        'views/service_report.xml',
        'views/service_report_template.xml',
        'views/service_report_by_email.xml',
        'views/views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
