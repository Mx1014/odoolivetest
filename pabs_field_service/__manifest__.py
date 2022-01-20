# -*- coding: utf-8 -*-
{
    'name': "Field Service Slots",

    'summary': """
       This module will add a plan calender and slots to field service""",

    'description': """
        This module will add a plan calender and slots to field service
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'industry_fsm', 'pabs_logistics_extra', 'project', 'sale', 'helpdesk', 'repair',  'pabs_repair', 'helpdesk_stock', 'helpdesk_fsm', 'helpdesk_repair', 'pabs_base', 'pabs_delivery_report', 'industry_fsm_report', 'pabs_repair', 'industry_fsm'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml',
        'views/business_line.xml',
        'views/field_plan_calendar_view_task.xml',
        'views/project.xml',
        'views/project_task_kanban_view.xml',
        'views/project_task_tree_view.xml',
        'views/project_task_fsm_search_view.xml',
        'views/project_task_form_view.xml',
        'views/batch_sequence.xml',
        'views/project_task_batch_views.xml',
        'views/field_plan_calendar_gantt_view.xml',
        'views/shift_field_plan_calendar_view.xml',
        'views/delivery_reminder.xml',
        'views/field_plan_calendar_view_sale.xml',
        'views/shift_field_plan_calendar_view_sale.xml',
        'views/shift_field_plan_calendar_view_task.xml',
        'views/create_fsm_task_view_form.xml',
        'views/crm_form_view.xml',
        'views/sale_order_views.xml',
        'wizards/field_plan_calendar_wizard_helpdesk_ticket.xml',
        'wizards/create_fsm_task_crm_form.xml',
        'wizards/field_plan_calendar_wizard_crm_ticket.xml',
        'wizards/cancel_task_batch_view.xml',
        'views/field_slot_creator_automation.xml',
        'views/logistics_team_views.xml',
        'views/menu_items.xml',
        'views/stock_picking.xml',
        'views/stock_picking_batch_form.xml',
        'data/report_paperformat.xml',
        'views/problem_views.xml',
        'reports/report_delivery_note.xml',
        'reports/split_service_worksheet_report_template.xml',
        'reports/field_service_task.xml',
        'reports/field_service_print.xml',
        'reports/split_service_worksheet_report_template_task.xml',
        'reports/split_inspection_worksheet_report_template_task.xml',
        'reports/split_service_worksheet_report_button.xml',
        'views/split_service_worksheet_template_views.xml',
        'views/room_floor_master.xml',
        'views/split_inspection_worksheet_template_views.xml',
        'views/repair_view.xml',
        'reports/split_inspection_worksheet_report_template.xml',
        'views/split_inspection_print_action.xml',


        # 'data/worksheet_template.xml',
        'reports/field_service_detailed_tripsheet_template.xml',
        'reports/detailed_tripsheet_button.xml',
        'reports/worksheet_custom_report_templates_inherit.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'auto_install': True,
}
