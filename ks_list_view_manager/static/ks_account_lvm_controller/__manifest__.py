# -*- coding: utf-8 -*-
{
    'name': "Account List View Manager Controller",

    'summary': """

         """,

    'description': """
	List View ,
	Advance Search ,
	Read/Edit Mode ,
	Dynamic List ,
	Hide/Show list view columns ,
	List View Manager ,
	Odoo List View ,
	Odoo Advanced Search ,
	Odoo Connector ,
	Odoo Manage List View ,
	Drag and edit columns ,
	Dynamic List View Apps ,
	Advance Dynamic Tree View ,
	Dynamic Tree View Apps ,
	Advance Tree View Apps ,
	List/Tree View Apps ,
	Tree/List View Apps  ,
	Freeze List View Header ,
	List view Advance Search ,
	Tree view Advance Search ,
	Best List View Apps ,
	Best Tree View Apps ,
	Tree View Apps ,
	List View Apps ,
	List View Management Apps ,
	Treeview ,
	Listview ,
	Tree View ,
	one2many view,
        list one2many view,
        sticky header,
        report templates,
        sale order lists,
        approval check lists,
        pos order lists,
        orders list in odoo,
        top app,
        best app,
        best apps
    """,
    'author': "Ksolves India Ltd.",
    'sequence': 1,
    'website': "https://www.ksolves.com/",
    'live_test_url': 'https://listview.kappso.com/web/demo_login',
    'category': 'Tools',
    'version': '1.0.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'base_setup', 'ks_list_view_manager', 'account'],
    # always loaded
    'license': 'OPL-1',
    'currency': 'EUR',
    'price': 0.0,
    'maintainer': 'Ksolves India Ltd.',
    'support': 'sales@ksolves.com',
    'data': [
        'views/ks_assets.xml',
    ],

    'qweb': [
    ]

}
