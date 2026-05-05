# -*- coding: utf-8 -*-
{
    # App information
    'name': 'Smart Cleaning Management Solution | Cleaning Service Management System | Facility & Cleaning Management Software in Odoo',
    'category': 'Website',
    'version': '18.0.1.0',
    'summary': """
                """,

    'license': 'OPL-1',
    'description': "",

    # Dependencies
    'depends': ['base', 'website', 'hr', 'account', 'sale_timesheet'],

    # Views
    'data': [
        'data/service_type_data.xml',
        'data/cleaning_shift_data.xml',
        'data/project_data.xml',
        # 'data/email_template.xml',
        'security/ir.model.access.csv',
        'views/booking_request_view.xml',
        'views/service_type_vts_view.xml',
        'views/cleaning_shift_view.xml',
        'views/cleaning_team_view.xml',
        'views/project_task_view.xml',
        'views/hr_employee_view.xml',
        'views/booking_dashboard_view.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'cleaning_service_management_vts/static/src/js/dashboard.js',
            'cleaning_service_management_vts/static/src/xml/dashboard.xml',
            'cleaning_service_management_vts/static/src/css/dashboard.css',
        ],
    },

    # Odoo Store Specific
    'images': [],

    # Author
    'author': 'Vraja Technologies',
    'website': 'http://www.vrajatechnologies.com',
    'maintainer': 'Vraja Technologies',
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',

    # Technical
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': '',
    'currency': 'EUR',
}
