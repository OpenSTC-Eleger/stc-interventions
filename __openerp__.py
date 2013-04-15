# -*- coding: utf-8 -*-
##############################################################################
#
#   Openstc-oe
#
##############################################################################

{
    "name": "openstc_prets",
    "version": "0.1",
    "depends": ["purchase", "project", "board","product", "stock", "hotel_reservation", "email_template"],
    "author": "PYF & BP",
    "shortdesc":"openstc",
    "category": "Category",
    "description": """
    Module STC For Prêts, temporary module to store changes specific to prets untested features on SWIF 
    """,
    "data": [
        'security/openstc_security.xml',
        'views/openstc_pret_data.xml',
        'security/ir.model.access.csv',

        'wizard/create_task_view.xml',
        'wizard/ask_refused_view.xml',
        'wizard/ask_modify_service.xml',
        "wizard/openstc_pret_view_wizard.xml",

        'views/openstc_view.xml',
        "views/openstc_pret_checkout_view.xml",
        "views/openstc_pret_view.xml",
        'views/openstc_pret_menus_view.xml',

        'workflow/ask.xml',
        "workflow/openstc_pret_workflow.xml",
        'workflow/purchase_workflow.xml',

        "report/openstc_pret_qte_dispo_report_view.xml",
        "unit_tests/unit_tests.xml",

    ],
    "demo": [],
    "test": [],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
