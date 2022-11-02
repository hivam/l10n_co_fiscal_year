# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Fiscal Year',
    'version': '1.0',
    'category': 'fisca_year',
    'summary': 'l10n_co_fical_year',
    'description': """
    """,
    'website': '',
    'depends': ['account', 'base'],
    'data': [
        'views/view_account_fiscalyear.xml',
        'views/view_account_period.xml'
    ],
    'demo': [
    ],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
