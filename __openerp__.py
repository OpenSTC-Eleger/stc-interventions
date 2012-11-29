# -*- coding: utf-8 -*-
##############################################################################
#
#   Openstc-oe
#
##############################################################################

{
    "name": "openstc",
    "version": "0.1",
    "depends": ["project", "board","product", "stock", "hotel_reservation", "email_template"],
    "author": "PYF & BP",
    "category": "Category",
    "description": """
    Module STC
    """,
    "data": [
        'security/openstc_security.xml',
        'security/ir.model.access.csv',

        'wizard/create_task_view.xml',
        'wizard/ask_refused_view.xml',
        'wizard/ask_modify_service.xml',
        'views/openstc_view.xml',

        'views/openstc_view.xml',
        'workflow/ask.xml',
    ],
    "demo": [],
    "test": [],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
