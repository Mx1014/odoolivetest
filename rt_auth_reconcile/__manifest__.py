{
    'name': 'RT Reconcile Filter Fields',
    'version': '1.1',
    'author': 'Rolustech',
    'summary': 'Additional Reconcile Filter Fields for Auth Code and BenefitPay Code',
    'sequence': '1',
    'description': 'Additional Reconcile Filter Fields for Auth Code and BenefitPay Code',
    'category': 'Reconcile',
    'website': 'https://www.rolustech.com',
    'depends': ['account','pabs_sale'],
    'data': [
        "view/view.xml",
        "view/assets.xml"
        ],
    'qweb': ["static/src/xml/account_reconciliation.xml"],
    'installable': True,
    'application': True,
}
