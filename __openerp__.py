# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) 2012 SICLIC http://siclic.fr
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
#############################################################################

{
    "name": "openstc",
    "version": "0.1",
    "depends": ["web", "web_calendar","base","openbase","purchase", "project", "board","product", "stock", "hotel_reservation", "email_template"],
    "author": "PYF & BP",
    "shortdesc":"openstc",
    "category": "SICLIC",
    "description": """
    Module STC, technical services management (calendar, board, ...)
    """,
    "data": [
        'security/openstc_security_inter.xml',
        'security/ir.model.access.csv',

        'wizard/create_task_view.xml',
        'wizard/ask_refused_view.xml',
        'wizard/ask_modify_service.xml',

        'views/openstc_view_inter.xml',

        'data/openstc_mail.xml',
        'data/openstc_data.xml',

        'workflow/openstc_workflow.xml',
        "unit_tests/unit_tests.xml",

    ],
    "demo": [],
    "test": [],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
