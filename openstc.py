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
#    the Free Software Foundation, either version 3 of the License, ors_user
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
#import logging

import types

import logging
import netsvc
import pytz
from osv.orm import browse_record, browse_null
from osv import fields, osv, orm
from datetime import datetime
from tools.translate import _

#_logger = logging.getLogger(__name__

def _get_request_states(self, cursor, user_id, context=None):
    return (
                ('wait', 'Wait'),('confirm', 'To be confirm'),('valid', 'Valid'),('refused', 'Refused'),('closed', 'Closed')
            )

def _get_param(params, key):
    if params.has_key(key) == True :
        if params[key]!=None or params[key]!='' or params[key]>0 :
            return params[key]
    return False;


def _test_params(params, keys):
    param_ok = True
    for key in keys :
        if params.has_key(key) == False :
            param_ok = False
        else :
            if params[key]==None or params[key]=='' or params[key]==0 :
                param_ok = False
    return param_ok


def send_email(self, cr, uid, ids, params, context=None):
#def send_email( params ):
    #print("test"+params)
    ask_obj = self.pool.get('openstc.ask')
    ask = ask_obj.browse(cr, uid, ids[0], context)

    user_obj = self.pool.get('res.users')
    user = user_obj.read(cr, uid, uid,
                                    ['company_id'],
                                    context)

    company_obj = self.pool.get('res.company')
    company = company_obj.read(cr, uid, user['company_id'][0],
                            ['email'],
                            context)

    email_obj = self.pool.get("email.template")
    ir_model = self.pool.get("ir.model").search(cr, uid, [('model','=',self._name)])

    email_tmpl_id = email_obj.create(cr, uid, {
                #'name':'modèle de mail pour résa annulée',
                'name':'Suivi de la demande ' + ask.name,
                'model_id':ir_model[0],
                'subject':'Suivi de la demande ' + ask.name,
                'email_from': company['email'],
                'email_to': ask.partner_email or ask.people_email or False,
                'body_text':"Votre Demande est à l'état " + params['email_text'] +  "\r" +
                    "pour plus d'informations, veuillez contacter la mairie de Pont L'abbé au : 0240xxxxxx"
        })

    mail_id = email_obj.send_mail(cr, uid, email_tmpl_id, ids[0])
    #to uncomment
    #self.pool.get("mail.message").send(cr, uid, [mail_id])

    return True

#----------------------------------------------------------
# Equipments
#----------------------------------------------------------

class equipment(osv.osv):
    _name = "openstc.equipment"
    _description = "openstc.equipment"
    #_inherit = 'product.product'
    _inherits = {'product.product': "product_product_id"}

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','type'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['type']:
                name =  name + ' / '+ record['type']
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

#    def create(self, cr, uid, data, context={}):
#        res = super(equipment, self).create(cr, uid, data, context)
#        return res
#
#    def write(self, cr, uid, data, context={}):
#        res = super(equipment, self).create(cr, uid, data, context)
#        return res

    _columns = {
            'immat': fields.char('Imatt', size=128),
            'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
            'product_product_id': fields.many2one('product.product', 'Product', help="", ondelete="cascade"),
            #Service authorized for use equipment
            'service_ids':fields.many2many('openstc.service', 'openstc_equipment_services_rel', 'equipment_id', 'service_id', 'Services'),
            #Service owner
            'service':fields.many2one('openstc.service', 'Service'),

            'marque': fields.char('Marque', size=128),
            'type': fields.char('Type', size=128),
            'usage': fields.char('Usage', size=128),

            'technical_vehicle': fields.boolean('Technical vehicle'),
            'commercial_vehicle': fields.boolean('Commercial vehicle'),

            'small_material': fields.boolean('Small'),
            'fat_material': fields.boolean('Fat'),

            'cv': fields.integer('CV', select=1),
            'year': fields.integer('Year', select=1),
            'time': fields.integer('Time', select=1),
            'km': fields.integer('Km', select=1),



            #Calcul total price and liters
            #'oil_qtity': fields.integer('oil quantity', select=1),
            #'oil_price': fields.integer('oil price', select=1),
    }


equipment()


#----------------------------------------------------------
# Services
#----------------------------------------------------------

class service(osv.osv):
    _name = "openstc.service"
    _description = "openstc.service"
    _rec_name = "name"

    _columns = {
            'name': fields.char('Name', size=128, required=True),
            'favcolor':  fields.char('Name', size=128),
            'code': fields.char('Code', size=32, required=True),
            'service_id':fields.many2one('openstc.service', 'Service Parent'),
            'category_ids':fields.many2many('openstc.task.category', 'openstc_task_category_services_rel', 'service_id', 'task_category_id', 'Categories'),
            'technical': fields.boolean('Technical service'),
            'manager_id': fields.many2one('res.users', 'Manager'),
            'asksBelongsto': fields.one2many('openstc.ask', 'service_id', "asks"),

            #'employees': fields.one2many('res.users', 'service_id', 'Employees'),
            #'user_ids': fields.many2many('res.users', 'openstc_user_services_rel', 'service_id', 'user_id', 'Employees'),
            'user_ids': fields.one2many('res.users', 'service_id', "Users"),
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

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','type'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['type']:
                name =  name + ' / '+ record['type'][1]
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _columns = {

            'name': fields.char('Name', size=128, required=True),
            'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
            'code': fields.char('Code', size=32),
            'type': fields.many2one('openstc.site.type', 'Type', required=True),
            'service_ids':fields.many2many('openstc.service', 'openstc_site_services_rel', 'site_id', 'service_id', 'Services'),
            #'service': fields.many2one('openstc.service', 'Service', required=True),
            'site_parent_id': fields.many2one('openstc.site', 'Site parent', help='Site parent', ondelete='set null'),
            'lenght': fields.integer('Lenght'),
            'width': fields.integer('Width'),
            'surface': fields.integer('Surface'),
            'long': fields.float('Longitude'),
            'lat': fields.float('Latitude'),
            'asksBelongsto': fields.one2many('openstc.ask', 'site1', "asks"),
            'intervention_ids': fields.one2many('project.project', 'site1', "Interventions", String="Interventions"),
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

#    def _get_services_list(self, cr, uid, context=None):
#        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
#        list = []
#        for service_id in user.service_ids:
#            list.append(service_id.id)
#        return list
#
#
#    def fields_get(self, cr, uid, fields=None, context=None):
#        res = super(res_partner, self).fields_get(cr, uid, fields, context)
#        list = self._get_services_list(cr, uid,context)
#        for field in res:
#            if field == "service_id":
#                res[field]['domain']=[('id','in',list)]
#        return res

    _columns = {
         'type_id': fields.many2one('openstc.partner.type', 'Type'),
         'service_id':fields.many2one('openstc.service', 'Service du demandeur'),
         'technical_service_id':fields.many2one('openstc.service', 'Service technique concerné'),
         'technical_site_id': fields.many2one('openstc.site', 'Default Site'),
         #'user_ids': fields.many2many('res.users', 'openstc_partner_users_rel', 'partner_id', 'user_id', 'Users'),

    }
res_partner()


class res_partner_address(osv.osv):
    _description ='Partner Addresses st'
    _name = 'res.partner.address'
    _inherit = "res.partner.address"
    _order = 'type, name'


    _columns = {
        'user_id': fields.many2one('res.users', 'User'),
    }

    def create(self, cr, uid, data, context=None):
        res = super(res_partner_address, self).create(cr, uid, data, context)
        self.create_account(cr, uid, [res], data, context)

        return res



    def write(self, cr, uid, ids, data, context=None):

        user_obj = self.pool.get('res.users')
        partner_address = self.read(cr, uid, ids[0],
                                    ['user_id'],
                                    context)

        if partner_address.has_key('user_id')!= False :
            if partner_address['user_id'] != False :
                user = user_obj.browse(cr, uid, partner_address['user_id'][0], context=context)
                if user.id != 0 and  _test_params(data, ['login','password','name','email'])!= False :
                    user_obj.write(cr, uid, [user.id], {
                                    'name': data['name'],
                                    'firstname': data['name'],
                                    'user_email': data['email'],
                                    'login': data['login'],
                                    'new_password': data['password'],
                            }, context=context)

            else :
                self.create_account(cr, uid, ids, data, context)



        res = super(res_partner_address, self).write(cr, uid, ids, data, context)
        return res

    def create_account(self, cr, uid, ids, params, context):
        if _test_params(params, ['login','password','name','email'])!= False :

            company_ids = self.pool.get('res.company').name_search(cr, uid, name='STC')
            if len(company_ids) == 1:
                params['company_id'] = company_ids[0][0]
            else :
                params['company_id'] = 1;

            user_obj = self.pool.get('res.users')

            group_obj = self.pool.get('res.groups')
            #Get partner group (code group=PART)
            group_id = group_obj.search(cr, uid, [('code','=','PART')])[0]
            user_id = user_obj.create(cr, uid,{
                    'name': params['name'],
                    'firstname': params['name'],
                    'user_email': params['email'],
                    'login': params['login'],
                    'new_password': params['password'],
                    'groups_id' : [(6, 0, [group_id])],
                    })
            self.write(cr, uid, ids, {
                    'user_id': user_id,
                }, context=context)


res_partner_address()

#----------------------------------------------------------
# Employees
#----------------------------------------------------------

#class openstc_groups(osv.osv):
#    """
#        A portal is a group of users with specific menu, widgets, and typically
#        restricted access rights.
#    """
#    _name = 'openstc.group'
#    _description = 'OpenSTC groups'
#    _inherits = {'res.groups': 'group_id'}
#
#    _columns = {
#        'group_id': fields.many2one('res.groups', required=True, ondelete='cascade',
#            string='Group',
#            help='The group corresponding to this portal'),
#        'code': fields.char('Code', size=128),
#        'perm_request_confirm' : fields.boolean('Demander la Confirmation'),
#    }
#
#openstc_groups()

class groups(osv.osv):
    _name = "res.groups"
    _description = "Access Groups"
    _inherit = "res.groups"
    _rec_name = 'full_name'

    _columns = {
        'code': fields.char('Code', size=128),
        'perm_request_confirm' : fields.boolean('Demander la Confirmation'),
    }

groups()

class users(osv.osv):
    _name = "res.users"
    _description = "res users st"
    _inherit = "res.users"
    _rec_name = "name"

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','firstname'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['firstname']:
                name =  record['firstname'] + '  '+  name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    #Calculates if agent belongs to 'arg' code group
    def _get_group(self, cr, uid, ids, fields, arg, context):
         res = {}
         user_obj = self.pool.get('res.users')
         group_obj = self.pool.get('res.groups')

         for id in ids:
            user = user_obj.read(cr, uid, id,['groups_id'],context)
            #Get 'arg' group (MANAGER or DIRECTOR)
            group_ids = group_obj.search(cr, uid, [('code','=', arg),('id','in',user['groups_id'])])
            res[id] = True if len( group_ids ) != 0 else False
         return res


    #Calculates the agents can be added to the team
    def _get_officers(self, cr, uid, ids, fields, arg, context):
        res = {}
        user_obj = self.pool.get('res.users')

        #get list of all agents
        all_officer_ids = user_obj.search(cr, uid, []);
        all_officers = user_obj.browse(cr, uid, all_officer_ids, context);


        for id in ids:

            officers = []
            managerTeamID = []


            #get list of all teams
            user = self.browse(cr, uid, id, context=context)
            if user.isDST:
                res[id] = all_officer_ids
            elif user.isManager :
                for service_id in user.service_ids :
                    for officer in all_officers:
                        if not officer.isDST :
                        #officer = user_obj.browse(cr, uid, officer_id, context)
                            if service_id in officer.service_ids:
                                officers.append(officer.id)
                res[id] = officers
            else:
                for team_id in user.manage_teams :
                    managerTeamID.append(team_id.id)
                if len(managerTeamID) > 0 :
                    for officer in all_officers:
                        if not officer.isDST :
                        #officer = user_obj.browse(cr, uid, officer_id, context)
                            for team_id in officer.team_ids :
                                if team_id.id in managerTeamID :
                                    officers.append(officer.id)
                                    break
                res[id] = officers


        return res

    _columns = {
            'firstname': fields.char('firstname', size=128),
            'lastname': fields.char('lastname', size=128),
            'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
            'service_id':fields.many2one('openstc.service', 'Service    '),
            'contact_id': fields.one2many('res.partner.address', 'user_id', "Partner"),
            'service_ids': fields.many2many('openstc.service', 'openstc_user_services_rel', 'user_id', 'service_id', 'Services'),
            'cost': fields.integer('Coût horaire'),
            'post': fields.char('Post', size=128),
            'position': fields.char('Grade', size=128),
            'arrival_date': fields.datetime('Date d\'arrivée'),
            'birth_date': fields.datetime('Date de naissance'),
            'address_home': fields.char('Address', size=128),
            'city_home': fields.char('City', size=128),
            'phone': fields.char('Phone Number', size=12),
            #'is_manager': fields.boolean('Is manager'),
            #'team_ids': fields.many2many('openstc.team', 'openstc_user_teams_rel', 'user_id', 'team_id', 'Teams'),
            'tasks': fields.one2many('project.task', 'user_id', "Tasks"),

            'team_ids': fields.many2many('openstc.team', 'openstc_team_users_rel', 'user_id', 'team_id', 'Teams'),
            'manage_teams': fields.one2many('openstc.team', 'manager_id', "Teams"),
            'isDST' : fields.function(_get_group, arg="DIRE", method=True,type='boolean', store=False), #DIRECTOR group
            'isManager' : fields.function(_get_group, arg="MANA", method=True,type='boolean', store=False), #MANAGER group

            'officer_ids' : fields.function(_get_officers, method=True,type='many2one', store=False),
    }

    def create(self, cr, uid, data, context={}):
        #_logger.debug('create USER-----------------------------------------------');
        res = super(users, self).create(cr, uid, data, context)

        company_ids = self.pool.get('res.company').name_search(cr, uid, name='STC')
        if len(company_ids) == 1:
            data['company_id'] = company_ids[0][0]
        else:
            data['company_id'] = 1;
        if data.has_key('isManager')!=False and data['isManager']==True :
            self.set_manager(cr, uid, [res], data, context)
        #TODO
        #else

        return res

    def write(self, cr, uid, ids, data, context=None):

        if data.has_key('isManager')!=False and data['isManager']==True :
            self.set_manager(cr, uid, ids, data, context)

        res = super(users, self).write(cr, uid, ids, data, context=context)
        return res

    def set_manager(self, cr, uid, ids, data,context):

        service_obj = self.pool.get('openstc.service')

        group_obj = self.pool.get('res.groups')
        #Get officer group (code group=OFFI)
        group_id = group_obj.search(cr, uid, [('code','=','OFFI')])[0]

        service_id = service_obj.browse(cr, uid, data['service_id'], context=context)
        #Previous manager become an agent
        manager = service_obj.read(cr, uid, data['service_id'],
                                    ['manager_id'], context)
        if manager and manager['manager_id']:
            self.write(cr, uid, [manager['manager_id'][0]], {
                    'groups_id' : [(6, 0, [group_id])],
                }, context=context)

        #Update service : current user is service's manager
        service_obj.write(cr, uid, data['service_id'], {
                 'manager_id': ids[0],
             }, context=context)


users()

class team(osv.osv):
    _name = "openstc.team"
    _description = "team stc"
    _rec_name = "name"


    #Calculates the agents can be added to the team
    def _get_free_users(self, cr, uid, ids, fields, arg, context):
        res = {}
        user_obj = self.pool.get('res.users')
        group_obj = self.pool.get('res.groups')

        for id in ids:
            #get current team object
            team = self.browse(cr, uid, id, context=context)
            team_users = []
            #get list of agents already belongs to team
            for user_record in team.user_ids:
                team_users.append(user_record.id)
            #get list of all agents
            all_users = user_obj.search(cr, uid, []);

            free_users = []
            for user_id in all_users:
                #get current agent object
                user = user_obj.read(cr, uid, user_id,['groups_id'],context)
                #Current agent is DST (DIRECTOR group)?
                group_ids = group_obj.search(cr, uid, [('code','=','DIRE'),('id','in',user['groups_id'])])
                #Agent must not be DST and not manager of team and no already in team
                if (len( group_ids ) == 0) and (user_id != team.manager_id.id) and (user_id not in team_users):
                    free_users.append(user_id)

            res[id] = free_users

        return res


    _columns = {
            'name': fields.char('name', size=128),
            'manager_id': fields.many2one('res.users', 'Manager'),
            'service_ids': fields.many2many('openstc.service', 'openstc_team_services_rel', 'team_id', 'service_id', 'Services'),
            'user_ids': fields.many2many('res.users', 'openstc_team_users_rel', 'team_id', 'user_id', 'Users'),
            'free_user_ids' : fields.function(_get_free_users, method=True,type='many2one', store=False),
            #'user_ids': fields.one2many('res.users', 'team_id', "Users"),
            'tasks': fields.one2many('project.task', 'team_id', "Tasks"),
    }


team()

#----------------------------------------------------------
# Tâches
#----------------------------------------------------------

class task(osv.osv):
    _name = "project.task"
    _description = "Task ctm"
    _inherit = "project.task"
    __logger = logging.getLogger(_name)

    #Overrides search method of project module
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        return super(task, self).search(cr, user, args, offset=offset, limit=limit, order=order, context=context, count=count)

    #Overrides _is_template method of project module
    def _is_template(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for task in self.browse(cr, uid, ids, context=context):
            res[task.id] = True
        return res



        # Compute: effective_hours, total_hours, progress
#    def _hours_get(self, cr, uid, ids, field_names, args, context=None):
#        res = {}
#        for task in self.browse(cr, uid, ids, context=context):
#            res[task.id] = {'effective_hours': task.effective_hours, 'total_hours': (task.remaining_hours or 0.0) + task.effective_hours}
#            res[task.id]['delay_hours'] = res[task.id]['total_hours'] - task.planned_hours
#            res[task.id]['progress'] = 0.0
#            if (task.remaining_hours + task.effective_hours):
#                res[task.id]['progress'] = round(min(100.0 * task.effective_hours/ res[task.id]['total_hours'], 99.99),2)
#            if task.state in ('done','cancelled'):
#                res[task.id]['progress'] = 100.0
#        return res

    #Calculates if agent belongs to 'arg' code group
    def _get_active(self, cr, uid, ids, fields, arg, context):
         res = {}
         user_obj = self.pool.get('res.users')
         task_obj = self.pool.get('project.task')
         team_obj = self.pool.get('openstc.team')
         project_obj = self.pool.get('project.project')

         user = user_obj.browse(cr, uid, uid,context)


         for id in ids:
            task = task_obj.browse(cr, uid, id, context=context)

            task_user_id = task_team_id = team_manager_id = task_project_id = project_service_id = False
            if isinstance(task.user_id, browse_null)!= True :
                task_user_id = task.user_id.id

            if isinstance(task.team_id, browse_null)!= True :
                task_team_id = task.team_id.id
                team = team_obj.browse(cr, uid, task.team_id.id, context=context)

            if task_team_id!= False :
                if isinstance(team.manager_id, browse_null)!= True :
                    team_manager_id = team.manager_id.id

            if isinstance(task.project_id, browse_null)!= True :
                task_project_id = task.project_id.id

            if task_project_id != False :
                project = project_obj.browse(cr, uid, task_project_id, context=context)
                try:
                   if isinstance(project.service_id, browse_null)!= True :
                       project_service_id = project.service_id.id
                except orm.except_orm, inst:
                     project_service_id = False

            belongsToOfficer = (task_user_id!=False and task_user_id == user.id) or (team_manager_id!=False and team_manager_id == task_user_id)
            belongsToTeam = task_team_id in ( t.id for t in user.team_ids )
            belongsToServiceManager = project_service_id in (s.id for s in user.service_ids) and user.isManager == True
            res[id] = True if belongsToOfficer or belongsToTeam or belongsToServiceManager or user.isDST else False
         return res



    _columns = {
        'active':fields.function(_get_active, method=True,type='boolean', store=False),
        #'active': fields.boolean('Active'),
        'ask_id': fields.many2one('openstc.ask', 'Demande', ondelete='set null', select="1"),
        'project_id': fields.many2one('project.project', 'Intervention', ondelete='set null'),
        'equipment_ids':fields.many2many('openstc.equipment', 'openstc_equipment_task_rel', 'task_id', 'equipment_id', 'Equipments'),
        #'equipment_id':fields.many2one('openstc.equipment', 'Equipment'),
        #'service_id': fields.related('project_id', 'service_id', type='many2one', string='Service', relation='openstc.service'),
        'parent_id': fields.many2one('project.task', 'Parent Task'),
        'intervention_assignement_id':fields.many2one('openstc.intervention.assignement', 'Assignement'),
        'absent_type_id':fields.many2one('openstc.absent.type', 'Type d''abscence'),
        'category_id':fields.many2one('openstc.task.category', 'Category'),
        'state': fields.selection([('absent', 'Absent'),('draft', 'New'),('open', 'In Progress'),('pending', 'Pending'), ('done', 'Done'), ('cancelled', 'Cancelled')], 'State', readonly=True, required=True,
                                  help='If the task is created the state is \'Draft\'.\n If the task is started, the state becomes \'In Progress\'.\n If review is needed the task is in \'Pending\' state.\
                                  \n If the task is over, the states is set to \'Done\'.'),
        #'dst_group_id': fields.many2one('res.groups', string='DST Group', help='The group corresponding to DST'),
        'team_id': fields.many2one('openstc.team', 'Team'),

        'km': fields.integer('Km', select=1),
        'oil_qtity': fields.float('oil quantity', select=1),
        'oil_price': fields.float('oil price', select=1),

        'cancel_reason': fields.text('Cancel reason'),




#        'planned_hours': fields.float('Planned print_on_orderHours', help='Estimated time to do the task, usually set by the project manager when the task is in draft state.'),
#        'effective_hours': fields.float('Effective Hours', help='Time spent'),
#        'remaining_hours': fields.float('Remaining Hours', digits=(16,2), help="Total remaining time, can be re-estimated periodically by the assignee of the task."),
#        'total_hours': fields.function(_hours_get, string='Total Hours', multi='hours', help="Computed as: Time Spent + Remaining Time.",
#            store = {
#                'project.task': (lambda self, cr, uid, ids, c={}: ids, ['effective_hours','remaining_hours', 'planned_hours'], 10),
#            }),
#        'progress': fields.function(_hours_get, string='Progress (%)', multi='hours', group_operator="avg", help="If the task has a progress of 99.99% you should close the task if it's finished or reevaluate the time",
#            store = {
#                'project.task': (lambda self, cr, uid, ids, c={}: ids, ['effective_hours','remaining_hours', 'planned_hours','state'], 10),
#            }),
#        'delay_hours': fields.function(_hours_get, string='Delay Hours', multi='hours', help="Computed as difference between planned hours by the project manager and the total hours of the task.",
#            store = {
#                'project.task': (lambda self, cr, uid, ids, c={}: ids, ['effective_hours','remaining_hours', 'planned_hours'], 10),
#            }),
    }

    _defaults = {'active': lambda *a: True, 'user_id':None}

#    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
#        return super(task, self).search(cr, user, args, offset=offset, limit=limit, order=order, context=context, count=count)

    def createOrphan(self, cr, uid, ids, params, context=None):

        task_obj = self.pool.get(self._name)

        self.updateEquipment(cr, uid, params, context)

        res = super(task, self).create(cr, uid, params, context)
        new_task = task_obj.browse(cr, uid, res, context)

        self.createWork(cr, uid, new_task, params, context)

        return res


    def reportHours(self, cr, uid, ids, params, context=None):

        #report_hours
        #remaining_hours

        task_obj = self.pool.get(self._name)
        #Get current task
        task = task_obj.browse(cr, uid, ids[0], context)
        #do nothing if task no found or not report hours
        if task==None or task == False : return False
        if not _get_param(params, 'report_hours') : return False

        project_obj = self.pool.get('project.project')
        ask_obj = self.pool.get('openstc.ask')
        #Get intervention's task
        if task.project_id!=None and task.project_id!=False :
            if task.project_id.id > 0 :
                project = project_obj.browse(cr, uid, [task.project_id.id], context=context)[0]
                #update intervention state
                if (project.state != 'template'):
                    #update intervention state  : pending because remaining_hours>0
                    project_obj.write(cr, uid, project.id, {
                        'state': 'pending',
                    }, context=context)

        #Prepare equipment list
        if params.has_key('equipment_ids') and len(params['equipment_ids'])>0 :
            equipments_ids = params['equipment_ids']
        else :
            equipments_ids = []
        #update mobile equipment kilometers
        self.updateEquipment(cr, uid, params, context)

        #Records report time
        self.createWork(cr, uid, task, params, context)

        self.__logger.warning('----------------- Write task %s ------------------------------', ids[0])
        #Update Task
        task_obj.write(cr, uid, ids[0], {
                'state': 'done',
                'date_start': task.date_start or _get_param(params, 'date_start'),
                'date_end': task.date_end or _get_param(params, 'date_end'),
                'team_id': task.team_id.id or _get_param(params, 'team_id'),
                'user_id': task.user_id.id or _get_param(params, 'user_id'),
                'equipment_ids': [[6, 0, equipments_ids]],
                'remaining_hours': 0,
                'km': 0 if params.has_key('km')== False else params['km'],
                'oil_qtity': 0 if params.has_key('oil_qtity')== False else params['oil_qtity'],
                'oil_price': 0 if params.has_key('oil_price')== False else params['oil_price'],
            }, context=context)



        ask_id = 0
        if project!=None :
            ask_id = project.ask_id.id



        if _test_params(params,['remaining_hours'])!=False:
           #Not finnished task : Create new task for planification
           task_obj.create(cr, uid, {
                 'name'              : task.name,
                 'parent_id'         : task.id,
                 'project_id'        : task.project_id.id or False,
                 'state'             : 'draft',
                 'planned_hours'     : 0 if params.has_key('remaining_hours')== False else params['remaining_hours'],
                 'remaining_hours'   : 0 if params.has_key('remaining_hours')== False else params['remaining_hours'],
                 'user_id'           : None,
                 'team_id'           : None,
                 'date_end'          : None,
                 'date_start'        : None,
             }, context)
        else:
            #Finnished task
            all_task_finnished = True

            #if task is the last at ['open','pending', 'draft'] state on intervention : close intervention and ask.
            for t in project.tasks :
                if task.id!=t.id and t.state in ['open','pending', 'draft']:
                    all_task_finnished = False
                    break

            if all_task_finnished == True:
                project_obj.write(cr, uid, project.id, {
                    'state': 'closed',
                }, context=context)

                if ask_id>0 :
                    ask_obj.write(cr, uid, ask_id, {
                        'state': 'closed',
                    }, context=context)

                #TODO
                #send email ==>  email_text: demande 'closed',

        return True


    def updateEquipment(self, cr, uid, params, context):
        equipment_obj = self.pool.get('openstc.equipment')
        #Update kilometers on vehucule
        if _test_params(params,['vehicule','km'])!= False :
            equipment_obj.write(cr, uid, params['vehicule'], {
                     'km': 0 if params.has_key('km')== False else params['km']
                 }, context=context)

    def createWork(self, cr, uid, task, params, context):
        task_work_obj = self.pool.get('project.task.work')
        #update task work

        task_work_obj.create(cr, uid, {
             'name': task.name,
             #TODO : manque l'heure
             'date':  datetime.now().strftime('%Y-%m-%d') if params.has_key('date')== False  else params['date'],
             'task_id': task.id,
             'hours':  _get_param(params, 'report_hours'),
             'user_id': task.user_id.id or False,
             'team_id': task.team_id.id or False,
             'company_id': task.company_id.id or False,
            }, context=context)

task()


class openstc_task_category(osv.osv):

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

#    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
#
#        return super(task, self).search(cr, user, args, offset=offset, limit=limit, order=order, context=context, count=count)

    _name = "openstc.task.category"
    _description = "Task Category"
    _columns = {
        'name': fields.char('Name', size=64, required=True, select=True),
        'code': fields.char('Code', size=32),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
        'parent_id': fields.many2one('openstc.task.category','Parent Category', select=True, ondelete='cascade'),
        'child_id': fields.one2many('openstc.task.category', 'parent_id', string='Child Categories'),
        'sequence': fields.integer('Sequence', select=True, help="Gives the sequence order when displaying a list of product categories."),
        'parent_left': fields.integer('Left Parent', select=1),
        'parent_right': fields.integer('Right Parent', select=1),
        'service_ids':fields.many2many('openstc.service', 'openstc_task_category_services_rel', 'task_category_id', 'service_id', 'Services'),
        'unit': fields.char('Unit', size=32),
        'quantity': fields.integer('Quantity'),
        'tasksAssigned': fields.one2many('project.task', 'category_id', "tasks"),
    }

    _sql_constraints = [
        ('category_uniq', 'unique(name,parent_id)', 'Category must be unique!'),
    ]


    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence, name'
    _order = 'parent_left'

    def _check_recursion(self, cr, uid, ids, context=None):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from openstc_task_category where id IN %s',(tuple(ids),))
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True

    _constraints = [
        (_check_recursion, 'Error ! You cannot create recursive categories.', ['parent_id'])
    ]
    def child_get(self, cr, uid, ids):
        return [ids]

openstc_task_category()



class openstc_absent_type(osv.osv):
    _name = "openstc.absent.type"
    _description = ""
    _columns = {
            'name': fields.char('Affectation ', size=128, required=True),
            'code': fields.char('Code affectation', size=32, required=True),
            'description': fields.text('Description'),
    }
openstc_absent_type()

#----------------------------------------------------------
# Interventions
#----------------------------------------------------------

#class account_analytic_account(osv.osv):
#    _inherit = "account.analytic.account"
#    _columns = {
#        'service_id':fields.many2one('openstc.service', 'Service'),
#        }
#account_analytic_account()

class project(osv.osv):
    _name = "project.project"
    _description = "Interventon stc"
    _inherit = "project.project"

    def _get_projects_from_tasks(self, cr, uid, task_ids, context=None):
        tasks = self.pool.get('project.task').browse(cr, uid, task_ids, context=context)
        project_ids = [task.project_id.id for task in tasks if task.project_id]
        return self.pool.get('project.project')._get_project_and_parents(cr, uid, project_ids, context)

    def _get_project_and_parents(self, cr, uid, ids, context=None):
        """ return the project ids and all their parent projects """
        res = set(ids)
        while ids:
            cr.execute("""
                SELECT DISTINCT parent.id
                FROM project_project project, project_project parent, account_analytic_account account
                WHERE project.analytic_account_id = account.id
                AND parent.analytic_account_id = account.parent_id
                AND project.id IN %s
                """, (tuple(ids),))
            ids = [t[0] for t in cr.fetchall()]
            res.update(ids)
        return list(res)

    #Overrides project : progress_rate ratio on planned_hours instead of 'total_hours'
    def _progress_rate(self, cr, uid, ids, names, arg, context=None):
        child_parent = self._get_project_and_children(cr, uid, ids, context)
        # compute planned_hours, total_hours, effective_hours specific to each project
        cr.execute("""
            SELECT project_id, COALESCE(SUM(planned_hours), 0.0),
                COALESCE(SUM(total_hours), 0.0), COALESCE(SUM(effective_hours), 0.0)
            FROM project_task WHERE project_id IN %s AND state <> 'cancelled'
            GROUP BY project_id
            """, (tuple(child_parent.keys()),))
        # aggregate results into res
        res = dict([(id, {'planned_hours':0.0,'total_hours':0.0,'effective_hours':0.0}) for id in ids])
        for id, planned, total, effective in cr.fetchall():
            # add the values specific to id to all parent projects of id in the result
            while id:
                if id in ids:
                    res[id]['planned_hours'] += planned
                    res[id]['total_hours'] += total
                    res[id]['effective_hours'] += effective
                id = child_parent[id]
        # compute progress rates
        for id in ids:
            if res[id]['planned_hours']:
                res[id]['progress_rate'] = round(100.0 * res[id]['effective_hours'] / res[id]['planned_hours'], 2)
            else:
                res[id]['progress_rate'] = 0.0
        return res


    def _tooltip(self, cr, uid, ids, myFields, arg, context):
        res = {}

        project_obj = self.pool.get('project.project')
        task_obj = self.pool.get('project.task')

        for id in ids:
            res[id] = ''
            inter = self.browse(cr, uid, id, context)
            if inter :
                first_date = None
                last_date = None
                allPlanned = True
                for task_id in inter.tasks :
                    task = task_obj.browse(cr, uid, task_id.id, context)
                    if  first_date == None :
                        first_date = task.date_start;
                    elif task.date_start and first_date>task.date_start :
                        first_date=task.date_start;

                    if last_date == None :
                        last_date = task.date_end;
                    elif task.date_end and last_date<task.date_end :
                        last_date=task.date_end

                    if task.state == 'draft' :
                        allPlanned = False

                if last_date :
                     last_date = fields.datetime.context_timestamp(cr, uid,
                            datetime.strptime(last_date, '%Y-%m-%d  %H:%M:%S')
                            , context)

                if first_date :
                     first_date = fields.datetime.context_timestamp(cr, uid,
                            datetime.strptime(first_date, '%Y-%m-%d  %H:%M:%S')
                            , context)


                if first_date :
                    if inter.progress_rate >= 100 :
                        res[id] = _(' Ended date ') + last_date.strftime(_("%A, %d %B %Y %H:%M").encode('utf-8')).decode('utf-8')
                    elif inter.progress_rate == 0 :
                        res[id] = _(' Scheduled start date ') + first_date.strftime(_("%A, %d %B %Y %H:%M").encode('utf-8')).decode('utf-8')

                    elif last_date and allPlanned:
                        res[id] = _(' Scheduled end date ') + last_date.strftime(_("%A, %d %B %Y %H:%M").encode('utf-8')).decode('utf-8')
                    else :
                        res[id] = _(' All tasks not planned ')

                if inter.state == 'cancelled' :
                    if inter.cancel_reason:
                      res[id] += inter.cancel_reason
                    else:
                      res[id] = _(' intervention cancelled ')

        return res


    def _overPourcent(self, cr, uid, ids, myFields, arg, context):
        res = {}

        project_obj = self.pool.get('project.project')
        task_obj = self.pool.get('project.task')

        for id in ids:
            res[id] = 0
            inter = self.browse(cr, uid, id, context)
            if inter :
                if inter.planned_hours :
                    res[id] = round(100.0 * inter.effective_hours / inter.planned_hours, 0);
        return res



    _columns = {

        'ask_id': fields.many2one('openstc.ask', 'Demande', ondelete='set null', select="1", readonly=True),
        'create_uid': fields.many2one('res.users', 'Created by', readonly=True),
        'create_date' : fields.datetime('Create Date', readonly=True),
        #'service_id': fields.related('ask_id', 'service_id', type='many2one', string='Service', relation='openstc.service'),
        'intervention_assignement_id':fields.many2one('openstc.intervention.assignement', 'Affectation'),
        'date_deadline': fields.date('Deadline',select=True),
        'site1': fields.many2one('openstc.site', 'Site principal'),
        #'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', help="Link this project to an analytic account if you need financial management on projects. It enables you to connect projects with budgets, planning, cost and revenue analysis, timesheets on projects, etc.", ondelete="cascade", required=False),
        'state': fields.selection([('closed', 'Closed'),('template', 'Template'),('open', 'Open'),('scheduled', 'Scheduled'),('pending', 'Pending'), ('closing', 'Closing'), ('cancelled', 'Cancelled')],
                                  'State', readonly=True, required=True, help=''),

        'service_id': fields.many2one('openstc.service', 'Service'),
        'description': fields.text('Description'),
        'site_details': fields.text('Précision sur le site'),
        'cancel_reason': fields.text('Cancel reason'),


        'progress_rate': fields.function(_progress_rate, multi="progress", string='Progress', type='float', group_operator="avg", help="Percent of tasks closed according to the total of tasks todo.",
            store = {
                'project.project': (_get_project_and_parents, ['tasks', 'parent_id', 'child_ids'], 10),
                'project.task': (_get_projects_from_tasks, ['planned_hours', 'remaining_hours', 'work_ids', 'state'], 20),
            }),

        'tooltip' : fields.function(_tooltip, method=True, string='Tooltip',type='char', store=False),
        'overPourcent' : fields.function(_overPourcent, method=True, string='OverPourcent',type='float', store=False),

    }

    #Overrides  set_template method of project module
    def set_template(self, cr, uid, ids, context=None):
        return True;

    def _get_active_inter(self, cr, uid, context=None):
        if context is None:
            return False
        else:
            return context.get('active_id', False)

    def _get_ask(self, cr, uid, context=None):
        inter_id = self._get_active_inter(cr, uid, context)
        if inter_id :
            ask_id = self.pool.get('project.project').read(cr, uid, inter_id,['ask_id'],context)['ask_id']
            if ask_id :
                ask_id[0]
        return False

    #Cancel intervention from swif
    def cancel(self, cr, uid, ids, params, context=None):
        #print("test"+params)
        project_obj = self.pool.get(self._name)
        project = project_obj.browse(cr, uid, ids[0], context)
        task_obj = self.pool.get('project.task')
        ask_obj = self.pool.get('openstc.ask')

        #update intervention's tasks
        if _test_params(params, ['state','cancel_reason'])!= False:
            for task in project.tasks:
                 task_obj.write(cr, uid, [task.id], {
                    'state' : params['state'],
                    'user_id': None,
                    'team_id': None,
                    'date_end': None,
                    'date_start': None,
                }, context=context)

            #update intervention with cancel's reason
            project_obj.write(cr, uid, ids[0], {
                    'state' : params['state'],
                    'cancel_reason': params['cancel_reason'],
                }, context=context)

            ask_id = project.ask_id.id
            #update ask state of intervention
            if ask_id :
                ask_obj.write(cr, uid, ask_id , {
                            'state': 'closed',
                        }, context=context)
                #TODO uncomment
                #send_email(self, cr, uid, [ask_id], params, context=None)
        return True;

    _defaults = {
        'ask_id' : _get_ask,
    }

    _sql_constraints = [
        ('ask_uniq', 'unique(name,ask_id)', 'Demande déjà validée!'),
    ]

project()


class intervention_assignement(osv.osv):
    _name = "openstc.intervention.assignement"
    _description = ""
    _columns = {
            'name': fields.char('Affectation ', size=128, required=True),
            'code': fields.char('Code affectation', size=32, required=True),
            'asksAssigned': fields.one2many('openstc.ask', 'intervention_assignement_id', "asks"),
    }
intervention_assignement()

class project_work(osv.osv):
    _name = "project.task.work"
    _description = "Task work"
    _inherit = "project.task.work"

    _columns = {
        'manager_id': fields.related('ask_id', 'manager_id', type='many2one', string='Services'),
        'user_id': fields.many2one('res.users', 'Done by', required=False, select="1"),
        'team_id': fields.many2one('openstc.team', 'Done by', required=False, select="1"),
    }

project_work()


class project_task_type(osv.osv):
    _name = "project.task.type"
    _description = "project.task.type"
    _inherit = "project.task.type"

    _columns = {

    }

project_task_type()


class project_task_history(osv.osv):
    _name = 'project.task.history'
    _description = 'History of Tasks'
    _inherit = "project.task.history"

    _columns = {
        'state': fields.selection([('closed', 'Closed'),('absent', 'Absent'),('draft', 'New'),('open', 'In Progress'),('pending', 'Pending'), ('done', 'Done'), ('cancelled', 'Cancelled')], 'State'),

    }

project_task_history()

class project_vs_hours(osv.osv):
    _name = "project.vs.hours"
    _description = " Project vs  hours"
    _inherit = "project.vs.hours"

    _columns = {

    }

project_vs_hours()



#----------------------------------------------------------
# Demandes
#----------------------------------------------------------
#class ir_rule(osv.osv):
#    _name = 'ir.rule'
#    _description = 'ir rule STC'
#    _inherit = 'ir.rule'
#    _MODES = ['read', 'write', 'create', 'unlink','confirm','valid','refuse']
#
#    _columns = {
#        'perm_confirm': fields.boolean('Apply For Confirm'),
#        'perm_valid': fields.boolean('Apply For Valid'),
#        'perm_refuse': fields.boolean('Apply For Refuse'),
#    }
#
#    _defaults = {
#        'perm_read': True,
#        'perm_write': True,
#        'perm_create': True,
#        'perm_unlink': True,
#        'perm_confirm': True,
#        'perm_valid': True,
#        'perm_refuse': True,
#        'global': True,
#    }
#
#ir_rule()


class ask(osv.osv):
    _name = "openstc.ask"
    _description = "openstc.ask"
    _order = "create_date desc"

    def _get_user_service(self, cr, uid, ipurchase_orderds, fieldnames, name, args):
        return False


    def _get_uid(self, cr, uid, context=None):
        return uid

    def _get_services(self, cr, uid, context=None):
        user_obj = self.pool.get('res.users')
        return user_obj.read(cr, uid, uid, ['service_ids'],context)['service_ids']

    def _is_possible_action(self, cr, uid, ids, fields, arg, context):
        res = {}
        user_obj = self.pool.get('res.users')
        group_obj = self.pool.get('res.groups')

        for id in ids:
            res[id] = []
            isDST = False
            isManager = False

            asks = self.read(cr, uid, [id], ['intervention_ids','service_id','state'], context=context)
            user = user_obj.read(cr, uid, uid,
                                        ['groups_id','service_ids'],
                                        context)
            #user is DST (DIRECTOR group, code group=DIRE)?
            group_ids = group_obj.search(cr, uid, [('code','=','DIRE'),('id','in',user['groups_id'])])
            if len( group_ids ) != 0:
                isDST = True

            #user is Manager (code group = MANA)?
            group_ids = group_obj.search(cr, uid, [('code','in',('DIRE','MANA'))])
            if set(user['groups_id']).intersection(set(group_ids)) :
                isManager = True

            ask = asks[0] or False
            if isManager and ask and ask.has_key('intervention_ids')!=False and ask.has_key('service_id') and user.has_key('service_ids')!=False :
                if len(ask['intervention_ids'])==0 and ask['service_id'][0] in user['service_ids']:
                        if ask['state'] == 'wait' :
                            res[id] = ['valid', 'refused']
                            if isDST == False:
                                res[id] = ['valid', 'refused', 'confirm']

                        if ask['state'] == 'confirm' :
                            res[id] = ['valid', 'refused']

                        if ask['state'] == 'refused' :
                            res[id] = ['valid']
                            if isDST == False:
                                res[id] = ['valid', 'confirm']

        return res

#    def _is_valid_action(self, cr, uid, ids, fields, arg, context):
#        res = self._is_possible_action(cr, uid, ids, fields, arg, context)
#        for id in res:
#            asks = self.read(cr, uid, [id], ['state'], context=context)
#            ask = asks[0] or False
#            if ask['state'] in arg:
#                res[id] = True;
#        return res
#
#    def _is_request_confirm_action(self, cr, uid, ids, fields, arg, context):
#        res = self._is_possible_action(cr, uid, ids, fields, arg, context)
#        for id in res:
#            asks = self.read(cr, uid, [id], ['state'], context=context)
#            group_obj = self.pool.get('res.groups')
#            group_ids = group_obj.search(cr, uid, [('code','=','DIRECTOR')])
#            ask = asks[0] or False
#            if ask['state'] in arg and len(group_ids)>0 :
#                res[id] = True;
#        return res
#
#    def _is_refuse_action(self, cr, uid, ids, fields, arg, context):
#        res = self._is_possible_action(cr, uid, ids, fields, arg, context)
#        for id in res:
#            asks = self.read(cr, uid, [id], ['state'], context=context)
#            ask = asks[0] or False
#            if ask['state'] in arg:
#                res[id] = True;
#        return res

    def _tooltip(self, cr, uid, ids, myFields, arg, context):
        res = {}

        ask_obj = self.pool.get('openstc.ask')
        project_obj = self.pool.get('project.project')
        task_obj = self.pool.get('project.task')
        user_obj = self.pool.get('res.users')

        for id in ids:
            res[id] = ''


            ask = ask_obj.browse(cr, uid, id, context)
            if ask :
                modifyBy = user_obj.browse(cr, uid, ask.write_uid.id, context).name
                if ask.state == 'valid' or ask.state == 'closed' :
                    for intervention_id in ask.intervention_ids :
                         first_date = None
                         last_date = None
                         intervention = project_obj.browse(cr, uid, intervention_id.id, context)
                         if intervention :
                             for task_id in intervention.tasks :
                                 task = task_obj.browse(cr, uid, task_id.id, context)
                                 if task :
                                     if first_date == None:
                                        first_date = task.date_start
                                     elif task.date_start and first_date > task.date_start :
                                        first_date = task.date_start

                                     if last_date == None:
                                        last_date = task.date_end
                                     elif task.date_end and last_date < task.date_end :
                                        last_date = task.date_end
                             user = user_obj.browse(cr, uid, intervention.create_uid.id, context)
                             res[id] = _(" By ")  + user.name

                             if last_date :
                                 last_date = fields.datetime.context_timestamp(cr, uid,
                                                        datetime.strptime(last_date, '%Y-%m-%d  %H:%M:%S')
                                                        , context)

                             if first_date :
                                 first_date = fields.datetime.context_timestamp(cr, uid,
                                                        datetime.strptime(first_date, '%Y-%m-%d  %H:%M:%S')
                                                        , context)

                             if ask.state == 'closed' :
                                 if intervention.state == 'closed':
                                     res[id] += _(' Ended date ') + last_date.strftime(_("%A, %d. %B %Y %H:%M").encode('utf-8')).decode('utf-8')
                                 else:
                                      if intervention.cancel_reason:
                                          res[id] += intervention.cancel_reason
                                      else:
                                          res[id] = _(' intervention cancelled ')


                             elif first_date :
                                 if intervention.progress_rate == 0 :
                                     res[id] += _(' Scheduled start date ') + first_date.strftime(_("%A, %d. %B %Y %H:%M").encode('utf-8')).decode('utf-8')
                                 elif intervention.progress_rate == 100 :
                                     res[id] += _(' Ended date ') + last_date.strftime(_("%A, %d. %B %Y %H:%M").encode('utf-8')).decode('utf-8')
                                 elif last_date:
                                     res[id] += _(' Scheduled end date ') + last_date.strftime(_("%A, %d. %B %Y %H:%M").encode('utf-8')).decode('utf-8')
                                 else :
                                      res[id] += _(" To plan ")
                             else:
                                 res[id] += _(" Not plan ")

                elif ask.state == 'refused' :
                    if ask.refusal_reason:
                        res[id] = ask.refusal_reason  + '\n('+ modifyBy +')';
                    else:
                        res[id] = _(' request refused ')

                elif ask.state == 'confirm' :
                    if ask.note:
                        res[id] = ask.note + '\n('+ modifyBy +')';
                    else:
                        res[id] = _(' request confirmed ')


        return res

    _columns = {
        'name': fields.char('Asks wording', size=128, required=True, select=True),
        'create_date' : fields.datetime('Create Date', readonly=True, select=False),
        'create_uid': fields.many2one('res.users', 'Created by', readonly=True),
        'write_uid': fields.many2one('res.users', 'Created by', readonly=True),
        'current_date': fields.datetime('Date'),
        'confirm_by_dst': fields.boolean('Confirm by DST'),
        'description': fields.text('Description'),
        'intervention_ids': fields.one2many('project.project', 'ask_id', "Interventions", String="Interventions"),

        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='set null'),
        'partner_address': fields.many2one('res.partner.address', 'Contact',ondelete='set null'),


        'partner_type': fields.many2one('openstc.partner.type', 'Partner Type', required=True),
        'partner_type_code': fields.char('Partner code', size=128),

        'partner_phone': fields.related('partner_address', 'phone', type='char', string='Téléphone'),
        'partner_email': fields.related('partner_address', 'email', type='char', string='Email'),

        'people_name': fields.char('Name', size=128),
        'people_phone': fields.char('Phone', size=10),
        'people_email': fields.char('Email', size=128),

        'intervention_assignement_id':fields.many2one('openstc.intervention.assignement', 'Affectation'),
        'site1': fields.many2one('openstc.site', 'Site principal'),
        'site2': fields.many2one('openstc.site', 'Site secondaire'),
        'site3': fields.many2one('openstc.site', 'Place'),
        'site_details': fields.text('Précision sur le site'),
        'note': fields.text('Note'),
        'refusal_reason': fields.text('Refusal reason'),
        'manager_id': fields.many2one('res.users', 'Manager'),
        'partner_service_id': fields.related('partner_id', 'service_id', type='many2one', relation='openstc.service', string='Service du demandeur', help='...'),
        'service_id':fields.many2one('openstc.service', 'Service concerné'),
        'date_deadline': fields.date('Date souhaitée'),
        'state': fields.selection(_get_request_states, 'State', readonly=True,
                          help='If the task is created the state is \'Wait\'.\n If the task is started, the state becomes \'In Progress\'.\n If review is needed the task is in \'Pending\' state.\
                          \n If the task is over, the states is set to \'Done\'.'),

        'actions' : fields.function(_is_possible_action, method=True, string='Valider',type='selection', store=False),
        'tooltip' : fields.function(_tooltip, method=True, string='Tooltip',type='char', store=False),
#        'action_request_confirm' : fields.function(_is_possible_action, arg=['wait','refused'],
#                                                   method=True, string='Demander la Confirmation',type='boolean', store=False),
#        'action_refuse' : fields.function(_is_possible_action, arg=['wait','confirm'],
#                                          method=True, string='Refuser',type='boolean', store=False),

    }


    _defaults = {
        'name' : lambda self, cr, uid, context : context['name'] if context and 'name' in context else None,
        'state': '',
        'current_date': lambda *a: datetime.now().strftime('%Y-%m-%d'),
        'actions': [],
#        'action_valid' : False,
#        'action_request_confirm' : False,
#        'action_refuse' : False,
    }


#    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
#        res = super(ask, self).search(cr, user, args, offset=offset, limit=limit, order=order, context=context, count=count)
#        return res

    def create(self, cr, uid, data, context={}):
        data['state'] = 'wait'
        manager_id = self.pool.get('openstc.service').read(cr, uid, data['service_id'],['manager_id'],context)['manager_id']
        if manager_id:
            data['manager_id'] = manager_id[0]

        res = super(ask, self).create(cr, uid, data, context)
        #TODO uncomment
        #send_email(self, cr, uid, [res], data, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        isList = isinstance(ids, types.ListType)
        if isList == False :
            ids = [ids]
        res = super(ask, self).write(cr, uid, ids, vals, context=context)
        #if vals and vals.has_key('email_text'):
            #TODO uncomment
            #send_email(self, cr, uid, ids, vals, context)
        return res


    #valid ask from swif
    def valid(self, cr, uid, ids, params, context=None):
        ask_obj = self.pool.get(self._name)
        ask = ask_obj.browse(cr, uid, ids[0], context)
        project_obj = self.pool.get('project.project')
        task_obj = self.pool.get('project.task')

        #update ask with concerned service
        ask_obj.write(cr, uid, ids[0], {
                'state': params['request_state'],
                'description': params['description'],
                'intervention_assignement_id': params['intervention_assignement_id'],
                'service_id':  params['service_id'],
                'email_text': params['email_text'],
            }, context=context)

        #create intervention
        project_id = project_obj.create(cr, uid, {
                'ask_id': ask.id,
                'name': ask.name,
                'date_deadline': params['date_deadline'],
                'description': params['description'],
                'state': params['project_state'],
                'site1': params['site1'],
                'service_id':  params['service_id'],
            }, context=context)

        if params['create_task'] :
            #create task
            task_obj.create(cr, uid, {
                 'project_id': project_id,
                 'name': ask.name,
                 'planned_hours': params['planned_hours'],
                 'category_id': params['category_id'],
                }, context=context)
        #TODO : after configuration mail sender uncomment send_mail function
        #send_email(self, cr, uid, ids, params, context=None)
        return True


    def action_valid(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        document = self.browse(cr, uid, ids)[0]
        data_obj = self.pool.get('ir.model.data')
        form_view = data_obj.get_object_reference(cr, uid, 'openstc', 'view_openstc_ask_form2')
        action_id = self.pool.get('ir.actions.act_window').search(cr, uid, [("name", "=", "Intervention asks")], context=context)
        action_obj = self.pool.get('ir.actions.act_window').browse(cr, uid, action_id, context=context)[0]
        res = {}
        if action_obj:
            res = {
                'name' : 'Mentions',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_id': int(document.id),
                'view_id': action_obj.view_id and [action_obj.view_id.id] or False,
                'views': [(form_view and form_view[1] or False, 'form')],
                'res_model': action_obj.res_model,
                'type': action_obj.type,
                'target': 'new',
                }
        return res


    def action_valid_ok(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'valid'}, context=context)
        this = self.browse(cr, uid, ids[0], context=context)
        intervention_obj = self.pool.get('project.project')
        intervention_id = intervention_obj.create(cr, uid, {
                #'qualifier_id': uid,
                'name': this.name or 'A completer',
                'date_deadline': this.date_deadline,
                #'user_id': this.intervention_manager.id,
                'site1': this.site1.id,
                'ask_id': this.id,
            }, context=context)


        data_obj = self.pool.get('ir.model.data')
        action_id = self.pool.get('ir.actions.act_window').search(cr, uid, [("name", "=", "Intervention asks")], context=context)
        action_obj = self.pool.get('ir.actions.act_window').browse(cr, uid, action_id, context=context)[0]
        res = {}
        if action_obj:
            res = {
                'view_mode': 'tree,form',
                'res_model': action_obj.res_model,
                'type': action_obj.type,
                }
        return res

    def action_to_be_confirm(self, cr, uid, ids, context=None):
         #TODO send email to DST
         return self.write(cr, uid, ids, {'state': 'confirm'}, context=context)

    def action_confirm(self, cr, uid, ids, context=None):
         #TODO send email to chef de service
         return self.write(cr, uid, ids, {'state': 'wait', 'confirm_by_dst': True}, context=context)

    def action_refused(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj._get_id(cr, uid, 'openstc', 'action_openstc_refused_ask_view')
        if result:
            id = mod_obj.read(cr, uid, [result], ['res_id'])[0]['res_id']
        result = {}
        if not id:
            return result
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['target'] = 'new'
        return result

    def action_wait(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'wait'}, context=context)

    def unlink(self, cr, uid, ids, context=None):
        for mydocument in self.browse(cr, uid, ids):
            if mydocument.intervention_ids!=None and len(mydocument.intervention_ids) > 0:
                raise osv.except_osv(_('Suppression Impossible !'),_('Des interventions sont liées à la demande'))
            else:
                return super(ask, self).unlink(cr, uid, ids, context=context)

    def onChangePartner(self, cr, uid, ids, partner_id, context=None):
        res = {}
        if partner_id :
            partner_obj = self.pool.get('res.partner')
            partner = partner_obj.browse(cr, uid, partner_id, context)
            addresses = partner_obj.address_get(cr, uid, [partner.id])
            res['value'] = {
                'partner_address': addresses['default'],
                'partner_phone' : partner.phone,
                'partner_email': partner.email,
                'site1': partner.technical_site_id.id,
                'service_id': partner.technical_service_id.id,
                'partner_service_id': partner.service_id.id,
            }
        else :
            res['value'] = {
                'partner_id' : False,
                'partner_address': False,
                'partner_phone' : '',
                'partner_email': '',
                'site1': False,
                'service_id': '',
                'partner_service_id': '',
            }
        return res

    def onChangePartnerType(self, cr, uid, ids, partner_type, context=None):
        res = {}
        partner_type_obj = self.pool.get('openstc.partner.type')
        partner_type_code = partner_type_obj.read(cr, uid, partner_type, ['code'],context)['code']

        if partner_type_code:
            res['partner_type_code'] = partner_type_code
            res['partner_id'] = False
            res['partner_address'] = None
            res['partner_phone'] = ''
            res['partner_email'] = ''
            res['site1'] = None
            res['service_id'] = ''
            res['partner_service_id'] = ''
        else:
            res['partner_id'] = False
            res['partner_address'] = None
            res['partner_phone'] = ''
            res['partner_email'] = ''
            res['site1'] = None
            res['service_id'] = ''
            res['partner_service_id'] = ''

        return {'value': res}

    def onChangePartnerAddress(self, cr, uid, ids, partner_address, context=None):
        res = {}
        if partner_address :
            partner_address_obj = self.pool.get('res.partner.address')
            partner_address = partner_address_obj.browse(cr, uid, partner_address, context)
            res['value'] = {
                'partner_phone' : partner_address.phone,
                'partner_email': partner_address.email,
            }
        else :
            res['value'] = {
                'partner_phone' : '',
                'partner_email': '',
            }
        return res




ask()


#----------------------------------------------------------
# Others
#----------------------------------------------------------

class openstc_planning(osv.osv):
    _name = "openstc.planning"
    _description = "Planning"

    _columns = {
        'name': fields.char('Planning', size=128),
    }

openstc_planning()


class todo(osv.osv):
    _name = "openstc.todo"
    _description = "todo stc"
    _rec_name = "title"

    _columns = {
            'title': fields.char('title', size=128),
            'completed': fields.boolean('Completed'),
    }
todo()