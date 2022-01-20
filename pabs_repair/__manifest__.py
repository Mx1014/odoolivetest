# -*- coding: utf-8 -*-
{
    'name': "pabs_repair",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'repair', 'project', 'hr_timesheet', 'helpdesk', 'helpdesk_repair', 'stock', 'stock_account',
                'mail', 'product_brand', 'sale', 'pabs_warranty', 'pabs_logistics_extra', 'pabs_delivery_report',
                'account'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'data/data.xml',
        'data/report_paperformat.xml',
        'views/repair_settings.xml',
        'views/stock_picking.xml',
        'views/issue_type_views.xml',
        'views/repair_view.xml',
        'views/helpdesk.xml',
        'views/complaint_form_template.xml',
        'views/complaint_form.xml',
        'views/complainy_form_by_email.xml',
        'views/agent_mail.xml',
        'views/repair_mail.xml',
        'views/project_task_view.xml',
        'views/helpdesk_team_form_view.xml',
        'views/product_view_form.xml',
        'wizards/stock_picking_collect_view.xml',
        'views/helpdesk_ticket_form_view.xml',
        'views/stock_location_view.xml',
        'views/report_fsm_repair_views.xml',
        'views/service_category_views.xml',
        'wizards/stock_picking_return_view.xml',
        'reports/report_delivery_note_inherit.xml',
        'views/other_ticket_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
