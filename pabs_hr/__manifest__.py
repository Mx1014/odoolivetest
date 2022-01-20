# -*- coding: utf-8 -*-
{
    'name': "pabs_hr",

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
    'depends': ['base', 'hr_payroll', 'hr', 'hr_holidays', 'hr_holidays_attendance', 'hr_work_entry',
                'hr_payroll_account', 'hr_skills'],

    # always loaded
    'data': [
        'data/report_paperformat.xml',
        'data/increment_wage_automation.xml',
        'data/sequence.xml',
        'data/activity_type.xml',
        'data/timeoff_type.xml',
        'wizard/increment_wages_wizard.xml',
        'wizard/payslip_popup.xml',
        'wizard/rejoin_wizard.xml',
        # 'src/img/alsalam.logo.jpg',
        'security/ir.model.access.csv',
        'security/hr_groups.xml',
        'static/src/xml/assets.xml',
        'views/hr_employee.xml',
        'views/anual_provision.xml',
        'views/indemnity_provision.xml',
        'views/hr_contract.xml',
        # 'views/hr_leave_type.xml',
        'views/hr_payslip.xml',
        'views/hr_overtimes.xml',
        'views/hr_salary_rule.xml',
        'views/provision_adjustment.xml',
        'views/report_hr_employee.xml',
        'views/payslip_report.xml',
        'views/hr_resume.xml',
        'views/report_annual_leave.xml',
        'views/attachment_form.xml',
        'views/menuitem.xml',
        'views/templates.xml',
        'views/hr_holidays.xml',
        'reports/report_annual_leave_template.xml',
        'reports/payslip_report_template.xml',
        'reports/payslip_report_template_head_letter.xml',
        # 'reports/joining_form.xml',
        'reports/salary_certificate.xml',

    ],
    'qweb': [
        'static/src/xml/kanban_button.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
