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
from datetime import datetime
import types

from osv import fields, osv
from tools.translate import _

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

        if data.has_key('login') and data.has_key('password'):

            user_obj = self.pool.get('res.users')

            user_id = user_obj.create(cr, uid,{
                    'name': data['name'],
                    'firstname': data['name'],
                    'user_email': data['email'],
                    'login': data['login'],
                    'new_password': data['password'],
                    'groups_id' : [(6, 0, [35])],
                    })

            self.write(cr, uid, [res], {
                    'user_id': user_id,
                }, context=context)

#            partner_obj = self.pool.get('res.partner')
#            partner_obj.write(cr, uid, [data['partner_id']], {
#                        'user_ids': [(6, 0, [user_id])],
#                     }, context=context)
        return res

    def write(self, cr, uid, ids, data, context=None):

        if data.has_key('login') and data.has_key('password'):
            user_obj = self.pool.get('res.users')
            partner_address = self.read(cr, uid, data['partner_id'],
                                        ['user_id'],
                                        context)


            user = user_obj.browse(cr, uid, [partner_address['user_id']], context=context)
            if user[0].id != 0:
                user_obj.write(cr, uid, [user_id[0].id], {
                                'name': data['name'],
                                'firstname': data['name'],
                                'user_email': data['email'],
                                'login': data['login'],
                                'new_password': data['password'],
                        }, context=context)

        res = super(res_partner_address, self).write(cr, uid, ids, data, context)
        return res


res_partner_address()

#----------------------------------------------------------
# Employees
#----------------------------------------------------------

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
            'is_manager': fields.boolean('Is manager'),
            #'team_ids': fields.many2many('openstc.team', 'openstc_user_teams_rel', 'user_id', 'team_id', 'Teams'),
            'tasks': fields.one2many('project.task', 'user_id', "Tasks"),

            'team_ids': fields.many2many('openstc.team', 'openstc_team_users_rel', 'user_id', 'team_id', 'Teams'),
    }

    def create(self, cr, uid, data, context={}):

        res = super(users, self).create(cr, uid, data, context)

        if data.has_key('isManager') and data['isManager']==True :
            service_obj = self.pool.get('openstc.service')

            service_id = service_obj.browse(cr, uid, data['service_id'], context=context)
            #Previous manager become an agent
            manager = service_obj.read(cr, uid, data['service_id'],
                                        ['manager_id'], context)
            if manager and manager['manager_id']:
                self.write(cr, uid, [manager['manager_id'][0]], {
                        'groups_id' : [(6, 0, [17])],
                    }, context=context)

            #Update service : this user is service's manager
            service_obj.write(cr, uid, data['service_id'], {
                     'manager_id': res,
                 }, context=context)

        return res

    def write(self, cr, uid, ids, data, context=None):

        if data.has_key('isManager') and data['isManager']==True :
            service_obj = self.pool.get('openstc.service')

            service_id = service_obj.browse(cr, uid, data['service_id'], context=context)
            #Previous manager become an agent
            manager = service_obj.read(cr, uid, data['service_id'],
                                        ['manager_id'], context)
            if manager and manager['manager_id']:
                self.write(cr, uid, [manager['manager_id'][0]], {
                        'groups_id' : [(6, 0, [17])],
                    }, context=context)

            #Update service : current user is service's manager
            service_obj.write(cr, uid, data['service_id'], {
                     'manager_id': ids[0],
                 }, context=context)



        res = super(users, self).write(cr, uid, ids, data, context=context)
        return res


users()

class team(osv.osv):
    _name = "openstc.team"
    _description = "team stc"
    _rec_name = "name"

    _columns = {
            'name': fields.char('name', size=128),
            'manager_id': fields.many2one('res.users', 'Manager'),
            'service_ids': fields.many2many('openstc.service', 'openstc_team_services_rel', 'team_id', 'service_id', 'Services'),
            'user_ids': fields.many2many('res.users', 'openstc_team_users_rel', 'team_id', 'user_id', 'Users'),
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

    _columns = {
        'active': fields.boolean('Active'),
        'ask_id': fields.many2one('openstc.ask', 'Demande', ondelete='set null', select="1"),
        'project_id': fields.many2one('project.project', 'Intervention', ondelete='set null'),
        'equipment_ids':fields.many2many('openstc.equipment', 'openstc_equipment_task_rel', 'task_id', 'equipment_id', 'Equipments'),
        #'equipment_id':fields.many2one('openstc.equipment', 'Equipment'),
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

    _defaults = {'active': lambda *a: True,}

    # Method called on mark task done from swif
    def saveTaskDone(self, cr, uid, ids, params, context=None):
        task_obj = self.pool.get(self._name)
        task = task_obj.browse(cr, uid, ids[0], context)
        task_work_obj = self.pool.get('project.task.work')
        project_obj = self.pool.get('project.project')
        ask_obj = self.pool.get('openstc.ask')
        equipment_obj = self.pool.get('openstc.equipment')

        #Update kilometers on vehucule
        equipment_obj.write(cr, uid, params['vehicule'], {
                 'km': params['km'],
             }, context=context)

        #Update intervention sate
        project_obj.write(cr, uid, task.project_id.id, {
                'state': params['project_state'],
            }, context=context)
        project = project_obj.browse(cr, uid, [task.project_id.id], context=context)
        ask_id = project[0].ask_id.id
        #Also close ask when intevention is closing
        if params['project_state'] == 'closed' and project[0]!=None and project[0].ask_id:
            ask_obj.write(cr, uid, ask_id, {
                    'state': params['project_state'],
                }, context=context)
            #TODO uncomment
            #send_email(self, cr, uid, [ask_id], params, context=None)

        #update task work
        task_work_obj.create(cr, uid, {
             'name': task.name,
             'date': params['date'],
             'task_id': task.id,
             'hours': params['hours'],
             'user_id': task.user_id.id or False,
             'team_id': task.team_id.id or False,
             'company_id': task.company_id.id or False,
            }, context=context)

        #update task
        task_obj.write(cr, uid, ids[0], {
                'state': params['task_state'],
                'equipment_ids': [[6, 0, params['equipment_ids']]],
                'remaining_hours': params['remaining_hours'],
                'km': params['km'],
                'oil_qtity': params['oil_qtity'],
                'oil_price': params['oil_price'],
            }, context=context)

        return True

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
        'service_ids':fields.many2many('openstc.task.category', 'openstc_task_category_services_rel', 'task_category_id', 'service_id', 'Services'),
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
    }


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


    _columns = {
        'name': fields.char('Asks wording', size=128, required=True, select=True),
        'create_date' : fields.datetime('Create Date', readonly=True),
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
        #'date_deadline': fields.date('Deadline',select=True),
        'state': fields.selection([('wait', 'Wait'),('confirm', 'To be confirm'),('valid', 'Valid'),('refused', 'Refused'),('closed', 'Closed')], 'State', readonly=True,
                          help='If the task is created the state is \'Wait\'.\n If the task is started, the state becomes \'In Progress\'.\n If review is needed the task is in \'Pending\' state.\
                          \n If the task is over, the states is set to \'Done\'.'),

    }


    _defaults = {
        'name' : lambda self, cr, uid, context : context['name'] if context and 'name' in context else None,
        'state': '',
        'current_date': lambda *a: datetime.now().strftime('%Y-%m-%d'),
    }



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