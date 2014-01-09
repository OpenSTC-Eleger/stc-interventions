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

        'workflow/ask.xml',
        "unit_tests/unit_tests.xml",

    ],
    "demo": [],
    "test": [],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
