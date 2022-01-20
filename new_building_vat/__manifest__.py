# -*- coding: utf-8 -*-

{
    'name': '(Sales) Change the VAT for New Building',
    'category': 'Operations/Inventory',
    'summary': 'Asks the salesperson to enter the documents needed for a new building VAT rules in Bahrain.',
    'description': """Asks the salesperson to enter the documents needed for a new building VAT rules in Bahrain.""",
    'version': '0.1',
    'depends': ['sale', 'pabs_sale_extra', 'pabs_sale', 'mail'],
    'data': [
        # 'security/groups.xml',
        'security/security.xml',
        'data/activity_type.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
}
