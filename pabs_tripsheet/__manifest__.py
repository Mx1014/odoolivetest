{
    'name': 'pabs_tripsheet',
    'category': 'Transfer',
    'summary': 'Tripshwwt Report Customization',
    'version': '1.0',
    'description': """Customization of ticket module as per requirement.""",
    'depends': ['base', 'stock', 'pabs_delivery_report'],
    'data': [
        'data/report_paperformat.xml',
        'reports/tripsheet_custom_template.xml',
        'reports/picking_list.xml',
        'reports/picking_operation.xml',
        'reports/detailed_tripsheet_report_template.xml',
        'views/detailed_tripsheet_report.xml',
        'views/stock_bitching_batch.xml',

    ],
    'installable': True,
    'auto_install': False,
}