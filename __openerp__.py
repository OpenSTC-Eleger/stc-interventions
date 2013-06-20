# -*- coding: utf-8 -*-

# OpenSTC Interventions - Openerp Module to manage Cityhall technical department
# Copyright (C) 2013 Siclic www.siclic.fr
#
# This file is part of OpenSTC Interventions.
#
# OpenSTC Interventions is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenSTC Interventions is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenSTC Interventions.  If not, see <http://www.gnu.org/licenses/>.

##############################################################################
#
#   Openstc-oe
#
##############################################################################

{
    "name": "openstc",
    "version": "0.1",
    "depends": ["web", "web_calendar","purchase", "project", "board","product", "stock", "hotel_reservation", "email_template"],
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

        'data/base_data.xml',
        #"unit_tests/openstc_prets_tests.xml",
        #"test/cr_commit.yml", "test/openstc_prets_tests.yml",
    ],
    #"test":"test/openstc_prets_tests.yml",
    "js":['static/src/js/calendar_inherit.js'],
    "demo": [],
    "test": [],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
