# -*- coding: utf-8 -*-
{
    'name': "events_extended",

    'summary': "Events Extended",

    'description': """Module
                   Technical
                   Test""",

    'author': "Reyes Hernando Santana Perez",
    'website': "inghernandosan@outlook.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '14.2',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'mail',
        'account',
        'stock',
    ],

    # always loaded
    'data': [
        'security/res_group_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/events_extended_view.xml',
        'views/event_type_view.xml',
        'views/event_hall_view.xml',
    ],
}
