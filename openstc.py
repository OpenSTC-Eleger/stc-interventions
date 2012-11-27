# -*- coding: utf-8 -*-

##############################################################################
#
#    OpenCivil module for OpenERP, module Etat-Civil
#    Copyright (C) 200X Company (<http://website>) pyf
#
#    This file is a part of penCivil
#
#    penCivil is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    penCivil is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import datetime

from osv import fields, osv
from tools.translate import _


#----------------------------------------------------------
# Services
#----------------------------------------------------------

class service(osv.osv):
    _name = "openstc.service"
    _description = "openstc.service"
    _rec_name = "name"

    _columns = {
            'name': fields.char('Name', size=128, required=True),
            'code': fields.char('Code', size=32, required=True),
            'service_id':fields.many2one('openstc.service', 'Service Parent'),
            #'category_ids':fields.many2many('openstc.task.category', 'openstc_task_category_services_rel', 'service_id', 'task_category_id', 'Categories'),
            'technical': fields.boolean('Technical service'),
            'manager_id': fields.many2one('res.users', 'Manager'),
    }
service()


#----------------------------------------------------------
# Sites
#----------------------------------------------------------

class site_type(osv.osv):
    _name = "openstc.site.type"
    _description = "openstc.site.type"

    _columns = {
            'name': fields.char('Name', size=128, required=True),
            'code': fields.char('Code', size=32, required=True),
    }
site_type()

class site(osv.osv):
    _name = "openstc.site"
    _description = "openstc.site"

    _columns = {

            'name': fields.char('Name', size=128, required=True),
            'code': fields.char('Code', size=32),
            'type': fields.many2one('openstc.site.type', 'Type', required=True),
            'service': fields.many2one('openstc.service', 'Service', required=True),
            'site_parent_id': fields.many2one('openstc.site', 'Site parent', help='Site parent', ondelete='set null'),
            'lenght': fields.integer('Lenght'),
            'width': fields.integer('Width'),
            'surface': fields.integer('Surface'),
    }

site()

#----------------------------------------------------------
# Partner
#----------------------------------------------------------

class openstc_partner_type(osv.osv):
    _name = "openstc.partner.type"
    _description = "openstc.partner.type"
    _rec_name = "name"

    _columns = {
            'name': fields.char('Name', size=128, required=True),
            'code': fields.char('Code', size=32, required=True),
            'claimers': fields.one2many('res.partner', 'type_id', "Claimers"),
    }
openstc_partner_type()

class res_partner(osv.osv):
    _name = "res.partner"
    _description = "res.partner"
    _inherit = "res.partner"
    _rec_name = "name"

    def _get_services_list(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        list = []
        for service_id in user.service_ids:
            list.append(service_id.id)
        return list


    def fields_get(self, cr, uid, fields=None, context=None):
        res = super(res_partner, self).fields_get(cr, uid, fields, context)
        list = self._get_services_list(cr, uid,context)
        for field in res:
            if field == "service_id":
                res[field]['domain']=[('id','in',list)]
        return res

    _columns = {
         'type_id': fields.many2one('openstc.partner.type', 'Type',required=True),
         'service_id':fields.many2one('openstc.service', 'Service du demandeur'),
         'technical_service_id':fields.many2one('openstc.service', 'Service technique concerné'),
         'technical_site_id': fields.many2one('openstc.site', 'Default Site'),

    }
res_partner()

#----------------------------------------------------------
# Employees
#----------------------------------------------------------

class users(osv.osv):
    _name = "res.users"
    _description = "res users ctm"
    _inherit = "res.users"
    _rec_name = "name"

    _columns = {
            'firstname': fields.char('firstname', size=128),
            'lastname': fields.char('lastname', size=128),
            'service_ids': fields.many2many('openstc.service', 'openstc_user_services_rel', 'user_id', 'service_id', 'Services'),
            'cost': fields.integer('Coût horaire'),
            'post': fields.char('Post', size=128),
            'position': fields.char('Grade', size=128),
            'arrival_date': fields.datetime('Date d\'arrivée'),
            'birth_date': fields.datetime('Date de naissance'),
            'address_home': fields.char('Address', size=128),
            'city_home': fields.char('City', size=128),
            'phone': fields.char('Phone Number', size=12),
            'is_manager': fields.boolean('Is manager'),
    }
users()





