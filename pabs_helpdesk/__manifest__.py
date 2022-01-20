{
    'name': 'pabs_helpdesk : pabs_helpdesk',
    'category': 'helpdesk',
    'summary': 'helpdeskCustomization',
    'version': '1.0',
    'description': """Customization of helpdesk module as per requirement.""",
    'depends': ['helpdesk', 'mail', 'product_brand', 'sale', 'pabs_warranty'],
    'data': [
        'views/helpdesk.xml',
        'views/agent_mail.xml',
        'views/customer_mail.xml',
        'data/report_paperformat.xml',
        'data/sequence.xml',
        'views/complaint_form.xml',
        'views/complaint_form_template.xml',

    ],
    'installable': True,
    'auto_install': False,
}