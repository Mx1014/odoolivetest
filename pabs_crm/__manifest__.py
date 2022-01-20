# -*- encoding: utf-8 -*-
{
    "name": "Pabs CRM",
    'version': '13.0.1.0.0',
    'author': 'Proadvisory Business Solution',
    'website': 'http://www.proadvisory.com',
    "depends": ["base", "crm", "sale", 'sale_crm', 'industry_fsm', 'pabs_field_service'],
    "category": "CRM",
    "data": [
       'secuirty/ir.model.access.csv',
       'views/lead_view_form.xml',
       'views/lead_type_view_form.xml',
    ],
    "init_xml": [],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
    #    'certificate': '',
}
