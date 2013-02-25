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
# Equipments
#----------------------------------------------------------

class equipment(osv.osv):
    _name = "openstc.equipment"
    _description = "openstc.equipment"
    _inherits = {'product.product': "product_product_id"}
    _rec_name = "name"

    _columns = {
            'name': fields.char('Imatt', size=128),
            'product_product_id': fields.many2one('product.product', 'Product', help="", ondelete="cascade", required=True),

            'marque': fields.char('Marque', size=128),
            'type': fields.char('Type', size=128),
            'usage': fields.char('Usage', size=128),
            'on_wheels': fields.boolean('On Wheels'),
            'small': fields.boolean('Small'),
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
            'code': fields.char('Code', size=32, required=True),
            'service_id':fields.many2one('openstc.service', 'Service Parent'),
            'category_ids':fields.many2many('openstc.task.category', 'openstc_task_category_services_rel', 'service_id', 'task_category_id', 'Categories'),
            'technical': fields.boolean('Technical service'),
            'manager_id': fields.many2one('res.users', 'Manager'),
            'asksBelongsto': fields.one2many('openstc.ask', 'service_id', "asks"),
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
            'asksBelongsto': fields.one2many('openstc.ask', 'site1', "asks"),
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
    _description = "res users st"
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
            #'team_ids': fields.many2many('openstc.team', 'openstc_user_teams_rel', 'user_id', 'team_id', 'Teams'),
            'tasks': fields.one2many('project.task', 'user_id', "Tasks"),
    }
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
        'equipment_id':fields.many2one('openstc.equipment', 'Equipment'),
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
        'oil_qtity': fields.integer('oil quantity', select=1),
        'oil_price': fields.integer('oil price', select=1),


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
        #'user_id': fields.many2one('res.users', 'Done by', required=False, select="1"),
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
        'date_deadline': fields.date('Deadline',select=True),
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
        return super(ask, self).create(cr, uid, data, context)

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

    def send_email(self, cr, uid, ids, params, context=None):
        #print("test"+params)
        ask_obj = self.pool.get('openstc.ask')
        ask = ask_obj.browse(cr, uid, ids[0], context)

        email_obj = self.pool.get("email.template")
        ir_model = self.pool.get("ir.model").search(cr, uid, [('model','=',self._name)])

        email_tmpl_id = email_obj.create(cr, uid, {
                    #'name':'modèle de mail pour résa annulée',
                    'name':'Suivi de la demande ' + ask.name,
                    'model_id':ir_model[0],
                    'subject':'Suivi de la demande ' + ask.name,
                    'email_from':'albacorefr@gmail.com',
                    'email_to': 'albacorefr@gmail.com', #ask.partner_email if ask.partner_email!=False else ask.people_email,
                    'body_text':"Votre Demande est à l'état " + _(ask.state) +  "\r" +
                        "pour plus d'informations, veuillez contacter la mairie de Pont L'abbé au : 0240xxxxxx"
            })

        mail_id = email_obj.send_mail(cr, uid, email_tmpl_id, ids[0])
        #self.pool.get("mail.message").write(cr, uid, [mail_id])
        self.pool.get("mail.message").send(cr, uid, [mail_id])

        return true;


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

