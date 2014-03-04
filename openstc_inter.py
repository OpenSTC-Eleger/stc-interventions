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
from openbase.openbase_core import OpenbaseCore
import re
import time
import operator
import logging
import netsvc
import pytz
from osv.orm import browse_record, browse_null
from osv import fields, osv, orm
from datetime import datetime, timedelta
from dateutil import *
from dateutil.tz import *

from tools.translate import _

#_logger = logging.getLogger(__name__)

def _get_request_states(self, cursor, user_id, context=None):
    return (
                ('wait', 'Wait'),('to_confirm', 'To be confirm'),('valid', 'Valid'),('refused', 'Refused'),('finished', 'Finished')
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


class service(OpenbaseCore):
    _inherit = "openstc.service"

    _columns = {
        'asksBelongsto': fields.one2many('openstc.ask', 'service_id', "asks"),
        'category_ids':fields.many2many('openstc.task.category', 'openstc_task_category_services_rel', 'service_id', 'task_category_id', 'Categories'),
    }

service()


class site(OpenbaseCore):
    _inherit = "openstc.site"
    _columns = {
        'asksBelongsto': fields.one2many('openstc.ask', 'site1', "asks"),
        'intervention_ids': fields.one2many('project.project', 'site1', "Interventions", String="Interventions"),
        }

class users(OpenbaseCore):
    _inherit = "res.users"
    _columns = {
            'tasks': fields.one2many('project.task', 'user_id', "Tasks"),
    }

class team(OpenbaseCore):
    _inherit = "openstc.team"
    _columns = {
        'tasks': fields.one2many('project.task', 'team_id', "Tasks"),

        }
team()

class res_partner(OpenbaseCore):
    _name = "res.partner"
    _description = "res.partner"
    _inherit = "res.partner"
    _rec_name = "name"



    _columns = {
         'service_id':fields.many2one('openstc.service', 'Service du demandeur'),
         'technical_service_id':fields.many2one('openstc.service', 'Service technique concerné'),
         'technical_site_id': fields.many2one('openstc.site', 'Default Site'),

    }
res_partner()

#----------------------------------------------------------
# Employees
#----------------------------------------------------------


#----------------------------------------------------------
# Tâches
#----------------------------------------------------------

class task(OpenbaseCore):
    _name = "project.task"
    _description = "Task ctm"
    _inherit = "project.task"
    __logger = logging.getLogger(_name)




    #Overrides _is_template method of project module
    def _is_template(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for task in self.browse(cr, uid, ids, context=context):
            res[task.id] = True
        return res




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

    def getUserTasksList(self, cr, uid, domain=[], fields=[], context=None):
        #in taskLists, absences are removed from result
        domain.extend([('state','!=','absent')])
        #first i get tasks with filter asked by UI
        res_ids = self.search(cr, uid, domain, context=context)
        res_filtered = [item[0] for item in self._get_active(cr, uid, res_ids, 'active', False, context=context).items() if item[1]]
        ret = self.read(cr, uid, res_filtered, fields, context=context)
        return ret

    #if tasks has an inter, returns service of this inter, else returns user services (returns empty list in unexpected cases)
    def get_services_authorized(self, cr, uid, id, context=None):
        ret = []
        if id:
            task = self.browse(cr, uid, id,context=context)
            if task.project_id:
                ret = [task.project_id.service_id and task.project_id.service_id.id] or []
            else:
                ret = self.pool.get("res.users").read(cr, uid, uid, ['service_ids'])['service_ids']
        else:
            ret = self.pool.get("res.users").read(cr, uid, uid, ['service_ids'])['service_ids']
        return ret

    def get_vehicules_authorized(self, cr, uid, id, context=None):
        service_id = self.get_services_authorized(cr, uid, id, context=context)
        ret = []
        if service_id:
            vehicule_ids = self.pool.get("openstc.equipment").search(cr, uid, ['&','|',('technical_vehicle','=',True),('commercial_vehicle','=',True),('service_ids','in',service_id)])
            ret = self.pool.get("openstc.equipment").read(cr, uid, vehicule_ids, ['id','name','type'],context=context)
        return ret

    def get_materials_authorized(self, cr, uid, id, context=None):
        service_id = self.get_services_authorized(cr, uid, id, context=context)
        ret = []
        if service_id:
            material_ids = self.pool.get("openstc.equipment").search(cr, uid, ['&','|',('small_material','=',True),('fat_material','=',True),('service_ids','in',service_id)])
            ret = self.pool.get("openstc.equipment").read(cr, uid, material_ids, ['id','name','type'],context=context)
        return ret

    #user can make survey of the task if it's an officer task, or a team task and user is a foreman / manager
    def _task_survey_rights(self, cr, uid, record, groups_code):
        ret = False
        if not record.team_id:
            ret = True
        else:
            ret = 'OFFI' not in groups_code
        return ret


    _fields_names = {'equipment_names':'equipment_ids'}

    _actions = {
        'print':lambda self,cr,uid,record, groups_code: record.state in ('draft','open'),
        'cancel':lambda self,cr,uid,record, groups_code: record.state == 'draft',
        'delete':lambda self,cr,uid,record, groups_code: record.state == 'draft',
        'replan': lambda self,cr,uid,record, groups_code: record.state == 'done',
        'normal_mode_finished': lambda self,cr,uid,record, groups_code: self._task_survey_rights(cr, uid, record, groups_code) and record.state == 'open',
        'normal_mode_unfinished': lambda self,cr,uid,record, groups_code: self._task_survey_rights(cr, uid, record, groups_code) and record.state == 'open',
        'light_mode_finished': lambda self,cr,uid,record, groups_code: self._task_survey_rights(cr, uid, record, groups_code) and record.state == 'draft',
        'light_mode_unfinished': lambda self,cr,uid,record, groups_code: self._task_survey_rights(cr, uid, record, groups_code) and record.state == 'draft',
        'modify': lambda self,cr,uid,record, groups_code: True,

        }

    def _get_task_from_inter(self, cr, uid, ids, context=None):
        return self.pool.get('project.task').search(cr, uid, [('project_id','in',ids)],context=context)

    _columns = {
        'active':fields.function(_get_active, method=True,type='boolean', store=False),
        'ask_id': fields.many2one('openstc.ask', 'Demande', ondelete='set null', select="1"),
        'project_id': fields.many2one('project.project', 'Intervention', ondelete='set null'),
        'equipment_ids':fields.many2many('openstc.equipment', 'openstc_equipment_task_rel', 'task_id', 'equipment_id', 'Equipments'),
        'parent_id': fields.many2one('project.task', 'Parent Task'),
        'intervention_assignement_id':fields.many2one('openstc.intervention.assignement', 'Assignement'),
        'absent_type_id':fields.many2one('openstc.absent.type', 'Type d''abscence'),
        'category_id':fields.many2one('openstc.task.category', 'Category'),
        'state': fields.selection([('absent', 'Absent'),('draft', 'New'),('open', 'In Progress'),('pending', 'Pending'), ('done', 'Done'), ('cancelled', 'Cancelled')], 'State', readonly=True, required=True,
                                  help='If the task is created the state is \'Draft\'.\n If the task is started, the state becomes \'In Progress\'.\n If review is needed the task is in \'Pending\' state.\
                                  \n If the task is over, the states is set to \'Done\'.'),
        'team_id': fields.many2one('openstc.team', 'Team'),

        'km': fields.integer('Km', select=1),
        'oil_qtity': fields.float('oil quantity', select=1),
        'oil_price': fields.float('oil price', select=1),
        'site1':fields.related('project_id','site1',type='many2one',relation='openstc.site', string='Site',store={'project.task':[lambda self,cr,uid,ids,ctx={}:ids, ['project_id'], 10],
                                                                                                                  'project.project':[_get_task_from_inter, ['site1'],11]}),
        'inter_desc': fields.related('project_id', 'description', type='char'),
        'inter_equipment': fields.related('project_id', 'equipment_id', type='many2one',relation='openstc.equipment'),
        'cancel_reason': fields.text('Cancel reason'),

    }

    _defaults = {'active': lambda *a: True, 'user_id':None}


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
        project = None
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
            if not isinstance(equipments_ids[0], list) and not isinstance(equipments_ids[0], tuple):
                equipments_ids = [(6,0,equipments_ids)]
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
                'team_id': task.team_id and task.team_id.id or _get_param(params, 'team_id'),
                'user_id': task.user_id and task.user_id.id or _get_param(params, 'user_id'),
                'equipment_ids': equipments_ids,
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
            if project != None and project:
                for t in project.tasks :
                    if task.id!=t.id and t.state in ['open','pending', 'draft']:
                        all_task_finnished = False
                        break

                if all_task_finnished == True:
                    project_obj.write(cr, uid, project.id, {
                        'state': 'finished',
                    }, context=context)

                    if ask_id>0 :
                        ask_obj.write(cr, uid, ask_id, {
                            'state': 'finished',
                        }, context=context)

                    #TODO
                    #send email ==>  email_text: demande 'finished',

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

    def create(self, cr, uid, vals, context=None):
        res = super(task, self).create(cr, uid, vals, context=context)
        #if task is created with reports_hours, update task_work and task values
        self.reportHours(cr, uid, [res], vals, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        #if we want to cancel task, we update some values automatically
        if 'state' in vals and vals['state'] == 'cancelled':
            for mTask in self.browse(cr, uid, ids, context=context):
                if mTask.state <> 'cancelled':
                    values = {}
                    values.update({'cancel_reason': _get_param(vals, 'cancel_reason') })
                    values.update({'remaining_hours': 0.0})
                    vals.update(values)
                    if not mTask.date_end:
                        vals.update({ 'date_end':time.strftime('%Y-%m-%d %H:%M:%S')})
                    super(task,self).write(cr, uid, [mTask.id],vals, context=context)
        else:
            res = super(task, self).write(cr, uid, ids, vals, context=context)
            #if task(s) have hours to report, we update task works and those tasks
            if not isinstance(ids, list):
                ids = [ids]
            self.reportHours(cr, uid, ids, vals, context=context)

        return True

    def cancel(self, cr, uid, ids, params, context={}):
        """
        Cancel Task
        """
        if not isinstance(ids,list): ids = [ids]
        for task in self.browse(cr, uid, ids, context=context):
            if task.state <> 'cancelled':
                vals = {}

                vals.update({'state': 'cancelled'})
                vals.update({'cancel_reason': _get_param(params, 'cancel_reason') })
                vals.update({'remaining_hours': 0.0})
                if not task.date_end:
                    vals.update({ 'date_end':time.strftime('%Y-%m-%d %H:%M:%S')})
                self.write(cr, uid, [task.id],vals, context=context)
            #message = _("The task '%s' is done") % (task.name,)
            #self.log(cr, uid, task.id, message)
        return True

    def planTasks(self, cr, uid, ids, params, context=None):

        """
        Plan tasks after drag&drop task on planning

        :param cr: database cursor
        :param uid: current user id
        :param ids: list of ids
        :param params: contains
            start_working_time : date/heure début de journée travaillée
            end_working_time : date/heure fin de journée
            start_lunch_time : date/heure début pause déjeuner
            end_lunch_time : date/heure fin pause déjeuner
            start_dt: date/heure du début de la plage souhaitée
            team_mode : boolean, calendrier d'une équipe ou d'un agent
            calendar_id : celui de l'agent / ou celui de l'équipe, selon le team_mode

        This method is used when plan tasks from client

        """

        self.log(cr, uid, ids[0], "planTasks")
        if not len(ids) == 1: raise Exception('Pas de tâche à planifier')

        #ret
        results = {}
        #date format
        timeDtFrmt = "%Y-%m-%d %H:%M:%S"

        #Get current task
        currentTask = self.browse(cr, uid, ids[0], context=context)
        #if task belongs to an intervention
        if currentTask.project_id:
            #Copy is true when intervention is a template
            copy = self.pool.get('project.project').is_template(cr, uid, [currentTask.project_id.id], context=context)


        if 'cpt' not in params:
            params['cpt'] = -1
            params["returnIds"] = [ids[0]]
        if 'number' not in params: params['number'] = 0
        #Init time to plan
        if 'timeToPlan' not in params: params['timeToPlan'] = currentTask.planned_hours
        #Planning is complete : return current task upgraded
        elif params['timeToPlan']==0 or not params['start_dt']:
            return  params["returnIds"]; #params['results']

        team_mode = params['team_mode']
        calendar_id = params['calendar_id']

        #Get all events on 'start_dt' for officer or team 'calendar_id'
        if 'events' not in params :
#            try:
            events = self.getTodayEventsById(cr, uid, ids, params, timeDtFrmt, context)
#            except Exception, e:
#                return e
        else:
            events = params['events']

        cpt = params['cpt']
        start_dt = params['start_dt']
        size = len(events)

        while True:
           cpt+=1
           #Get end date
           endDt = start_dt + timedelta(hours=params['timeToPlan'])
           if cpt<size:
               e = events[cpt]
               if(start_dt >= e['date_start'] and start_dt<=e['date_end']):
                    start_dt = e['date_end']
               elif start_dt > e['date_start']:
                    continue
               else:
                   break
           else:
               break


        if cpt  == size:
             #Task was not completely scheduled
            results.update({
                  'name':  currentTask.name,
                  'project_id': currentTask.project_id.id,
                  'parent_id': currentTask.id if copy else False,
                  'state': 'draft',
                  'planned_hours': params['timeToPlan'],
                  'remaining_hours': params['timeToPlan'],
                  'user_id': None,
                  'team_id': None,
                  'date_end': None,
                  'date_start': None,
            })
            #Return to plan with the remaining time
            self.write(cr, uid, [currentTask.id],results, context=context)
            params['timeToPlan'] = 0
            params['results'] = results
        else:
            #Get next date
            nextDt = events[cpt]['date_start']
            #hours differences to next date
            diff = (nextDt-start_dt).total_seconds()/3600

            if (params['timeToPlan'] - diff) == 0 :
                #whole task is completely schedulable (all hours) before next so timeToPlan is set to 0
                params['timeToPlan'] = 0
                endDt = nextDt
            elif (params['timeToPlan'] - diff) > 0 :
                #task is not completely schedulable
                params['timeToPlan'] = params['timeToPlan'] - diff
                endDt = nextDt
            else:
                #there is less time to plan the number of hours possible before the next date, diff is re-calculate
                params['timeToPlan'] = 0
                diff = (endDt-start_dt).total_seconds()/3600


            if params['number'] > 0 :
                #The task is divided : title is changed"
                title = "(Suite-" + str(params['number']) + ")" + currentTask.name
            else:
                title = currentTask.name

            results = {
                'name': title,
                'planned_hours': diff,
                'remaining_hours': diff,
                'team_id': calendar_id if team_mode else None,
                'user_id': calendar_id if not team_mode else None,
                'date_start': datetime.strftime(start_dt,timeDtFrmt),
                'date_end': datetime.strftime(endDt,timeDtFrmt),
                'state': 'open',
                'parent_id': currentTask.id if copy else False,
                'project_id': currentTask.project_id.id,
            }

            #All time is scheduled and intervention is not a template
            if params['timeToPlan'] == 0 and not copy:
                #Update task
               self.write(cr, uid, [currentTask.id],results, context=context)

            else:
                #Create task
                id = self.create(cr, uid, results);
                params["returnIds"].append(id)

        params['results'] = results
        params['start_dt'] = endDt
        params['number'] += 1
        params['cpt'] = cpt - 1
        #re-call the method with new params
        return self.planTasks(cr, uid, ids, params, context)

    def getTodayEventsById(self, cr, uid, ids, params, timeDtFrmt, context=None):
        """
        Plan tasks after drag&drop task on planning

        :param cr: database cursor
        :param uid: current user id
        :param ids: list of ids
        :param params: contains
            start_working_time : date/heure début de journée travaillée
            end_working_time : date/heure fin de journée
            start_lunch_time : date/heure début pause déjeuner
            end_lunch_time : date/heure fin pause déjeuner
            start_dt: date/heure du début de la plage souhaitée
            team_mode : boolean, calendrier d'une équipe ou d'un agent
            calendar_id : celui de l'agent / ou celui de l'équipe, selon le team_mode

        This method is used to get events on start_dt (lunch including) for officer or team (calendar_id)

        """
        if not set(('start_working_time','end_working_time','start_lunch_time','end_lunch_time','start_dt','calendar_id')).issubset(params) :
            raise Exception('Erreur : il manque des paramètres pour pouvoir planifier (Heure d''embauche, heure de déjeuner...) \n Veuillez contacter votre administrateur ')

        #Date format passed by javascript client : date from utc.
        #Client swif lose the timezone because of the serialisation in JSON request (JSON.stringify)
        timeDtFrmtWithTmz = "%Y-%m-%dT%H:%M:%S.000Z"
        #Get user context
        context_tz = self.pool.get('res.users').read(cr,uid,[uid], ['context_tz'])[0]['context_tz'] or 'Europe/Paris'
        tzinfo = pytz.timezone(context_tz)

        events= []

        todayDt = datetime.now(tzinfo)
        #Calculate time differencee between utc and user's timezone
        deltaTz = int((datetime.utcoffset(todayDt).total_seconds())/3600)

        #Get Start and end working time, lunch start and stop times
        start_dt = datetime.strptime(params['start_dt'],timeDtFrmtWithTmz)
        start_working_time = start_dt.replace(hour= (int(params['start_working_time'])-deltaTz),minute=0, second=0, microsecond=0)
        start_lunch_time = start_dt.replace( hour = (int(params['start_lunch_time'])-deltaTz),minute=0, second=0, microsecond=0 )
        end_lunch_time = start_dt.replace( hour = (int(params['end_lunch_time'])-deltaTz),minute=0, second=0, microsecond=0 )

        #Add in list
        events.append({'title': "lunchTime", 'date_start': start_lunch_time,
                       'date_end': end_lunch_time})
        end_working_time = start_dt.replace( hour = (int(params['end_working_time'])-deltaTz),minute=0, second=0, microsecond=0 )
        events.append({'title': "end_working_time", 'date_start': end_working_time,
                       'date_end': end_working_time})

        task_ids = []
        if params['team_mode'] == True:
            #Get all tasks on 'start_dt' for team
            task_ids = self.search(cr,uid,
                ['&',('date_start','>=', datetime.strftime(start_working_time,timeDtFrmt)),
                    ('date_start','<=', datetime.strftime(end_working_time,timeDtFrmt)),
                '|',('team_id','=',params['calendar_id']),
                    ('user_id','in', self.pool.get('openstc.team').read(cr, uid, params['calendar_id'], ['user_ids'])['user_ids'] )
                ])
        else:
            #Get all tasks on 'start_dt' for officer
            task_ids = self.search(cr,uid,
                ['&',('date_start','>=', datetime.strftime(start_working_time,timeDtFrmt)),
                    ('date_start','<=', datetime.strftime(end_working_time,timeDtFrmt)),
                 '|',('user_id','=', params['calendar_id']),
                    ('team_id','in', self.pool.get('res.users').read(cr, uid, params['calendar_id'], ['team_ids'])['team_ids'] )
                ])

        tasks = self.read(cr,uid,task_ids, ['name','date_start','date_end'])
        #Add tasks in list
        for task in tasks :
            events.append({'title': task['name'], 'date_start': datetime.strptime(task['date_start'],timeDtFrmt),
                           'date_end': datetime.strptime(task['date_end'],timeDtFrmt) })

        #Sort task
        events.sort(key=operator.itemgetter('date_start'))
        params['events'] = events
        params['start_dt'] = start_dt
        #Return tasks
        return events

task()

class openstc_task_category(OpenbaseCore):

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


    _actions = {
        'delete':lambda self,cr,uid,record, groups_code: 'DIRE' in groups_code,
        'update': lambda self,cr,uid,record, groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,
        'create': lambda self,cr,uid,record,groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,

    }

    _fields_names = {'service_names':'service_ids'}

    _name = "openstc.task.category"
    _description = "Task Category"
    _columns = {
        'name': fields.char('Name', size=64, required=True, select=True),
        'code': fields.char('Code', size=32),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Name', method=True, store={'openstc.task.category':[lambda self,cr,uid,ids,ctx={}:ids, ['name','parent_id'],10]}),
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
        ('category_uniq', 'unique(name,parent_id)', '*name* / Name and Category parent must be unique! Change name or category parent'),
        ('code_uniq', 'unique (code)', '*code* /codeNameUniq!')
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



class openstc_absent_type(OpenbaseCore):
    _name = "openstc.absent.type"
    _description = ""

    _actions = {
        'delete':lambda self,cr,uid,record, groups_code: 'DIRE' in groups_code,
        'update': lambda self,cr,uid,record, groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,
        'create': lambda self,cr,uid,record,groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,

    }

    _columns = {
            'name': fields.char('Affectation ', size=128, required=True),
            'code': fields.char('Code affectation', size=32, required=True),
            'description': fields.text('Description'),

    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', '*code* /codeNameUniq')
    ]
openstc_absent_type()

#----------------------------------------------------------
# Interventions
#----------------------------------------------------------


class project(OpenbaseCore):
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

    #if inter exists and is associated to a service, returns this service_id, else returns user services
    def get_services_authorized(self, cr, uid, id, context=None):
        if id:
            inter = self.browse(cr, uid, id, context=context)
            if inter.service_id:
                return [inter.service_id.id]

        return self.pool.get("res.users").read(cr, uid, uid, ['service_ids'])['service_ids']


    def get_task_categ_authorized(self, cr, uid, id, context=None):
        service_ids = self.get_services_authorized(cr, uid, id, context=context)
        ret = []
        if service_ids:
            task_ids = self.pool.get("openstc.task.category").search(cr, uid, [('service_ids','in',service_ids)])
            ret = self.pool.get("openstc.task.category").read(cr, uid, task_ids, ['id','name'])
        return ret

    _actions = {
        'cancel':lambda self,cr,uid,record,groups_code: record.state in ('open','scheduled'),
        'plan_unplan':lambda self,cr,uid,record,groups_code: (record.state == 'open' and not self.pool.get("project.task").search(cr, uid,[('state','=','draft'),('project_id','=',record.id)])) or record.state == 'scheduled' ,
        'add_task':lambda self,cr,uid,record,groups_code: record.state in ('open','template'),
        'print': lambda self,cr,uid,record,groups_code: True,
        'modify': lambda self,cr,uid,record,groups_code: True,
        'create': lambda self,cr,uid,record,groups_code: True,

        }


    def _searchOverPourcent(self, cr, uid, obj, name, args, context=None):
        if args and len(args[0]) >= 2:
            arg = args[0]
            where = ''
            if arg[2] is False:
                where = 'planned_hours = 0 or effective_hours / planned_hours = 0'
            else:
                where = 'planned_hours > 0 and 100 * effective_hours / planned_hours %s %s' % (arg[1], arg[2])
            cr.execute('select id from %s where %s' % (self._table, where))
            ret = cr.fetchall()
            return [('id','in',[item[0] for item in ret])]
        return [('id','>',0)]

    _columns = {

        'ask_id': fields.many2one('openstc.ask', 'Demande', ondelete='set null', select="1", readonly=True),
        'create_uid': fields.many2one('res.users', 'Created by', readonly=True),
        'create_date' : fields.datetime('Create Date', readonly=True, select=True),
        'intervention_assignement_id':fields.many2one('openstc.intervention.assignement', 'Affectation'),
        'date_deadline': fields.date('Deadline',select=True),
        'site1': fields.many2one('openstc.site', 'Site principal', select=True),
        'state': fields.selection([('finished', 'Finished'),('template', 'Template'),('open', 'Open'),('scheduled', 'Scheduled'),('pending', 'Pending'), ('cancelled', 'Cancelled')],
                                  'State', readonly=True, required=True, help=''),

        'service_id': fields.many2one('openstc.service', 'Service', select=True),
        'description': fields.text('Description', select=True),
        'site_details': fields.text('Précision sur le site'),
        'cancel_reason': fields.text('Cancel reason'),


        'progress_rate': fields.function(_progress_rate, multi="progress", string='Progress', type='float', group_operator="avg", help="Percent of tasks closed according to the total of tasks todo.",
            store = {
                'project.project': (_get_project_and_parents, ['tasks', 'parent_id', 'child_ids'], 9),
                'project.task': (_get_projects_from_tasks, ['planned_hours', 'remaining_hours', 'work_ids', 'state'], 19),
            }),

        'tooltip' : fields.function(_tooltip, method=True, string='Tooltip',type='char', store=False),
        'overPourcent' : fields.function(_overPourcent, fnct_search=_searchOverPourcent, method=True, string='OverPourcent',type='float', store=False),
        'equipment_id': fields.many2one('openstc.equipment','Equipment', select=True),
        'has_equipment': fields.boolean('Request is about equipment'),
    }

    #Overrides  set_template method of project module
    def set_template(self, cr, uid, ids, context=None):
        return True;

    def is_template(self, cr, uid, ids, context=None):
        if not(len(ids) == 1) : return false
        inter = self.pool.get('project.project').browse(cr, uid, ids[0], context=context)
        if isinstance(inter, browse_null)!= True :
            return inter.state == 'template' or False

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

    def write(self, cr, uid, ids, vals, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        res = super(project, self).write(cr, uid, ids, vals, context=context)
        task_obj = self.pool.get('project.task')
        ask_obj = self.pool.get('openstc.ask')
        #if we want to cancel inter, we cancel all tasks associated and close the parent ask
        if 'state' in vals and vals['state'] == 'cancelled':
            task_ids = task_obj.search(cr, uid, [('project_id.id','in',ids)],context=context)
            if task_ids:
                task_obj.write(cr, uid, task_ids, {'state':'cancelled',
                                                               'user_id':False,
                                                               'team_id':False,
                                                               'date_end':False,
                                                               'date_start':False,
                                                               'cancel_reason':vals.get('cancel_reason',False)},context=context)
            ask_ids = [item['ask_id'][0] for item in self.read(cr, uid, ids, ['ask_id'],context=context) if item['ask_id']]
            if ask_ids:
                ask_obj.write(cr, uid, ask_ids, {'state':'finished'})
            #TODO uncomment
            #send_email(self, cr, uid, [ask_id], params, context=None)

        return res

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
                            'state': 'finished',
                        }, context=context)
                #TODO uncomment
                #send_email(self, cr, uid, [ask_id], params, context=None)
        return True;

    _defaults = {
        'ask_id' : _get_ask,
        'has_equipment': False,
    }

    _sql_constraints = [
        ('ask_uniq', 'unique(name,ask_id)', 'Demande déjà validée!'),
    ]


project()


class intervention_assignement(OpenbaseCore):
    _name = "openstc.intervention.assignement"
    _description = ""

    _actions = {
        'create':lambda self,cr,uid,record, groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,
        'update':lambda self,cr,uid,record, groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,
        'delete':lambda self,cr,uid,record, groups_code: 'DIRE' in groups_code,

        }

    _columns = {
            'name': fields.char('Affectation ', size=128, required=True),
            'code': fields.char('Code affectation', size=32, required=True),
            'asksAssigned': fields.one2many('openstc.ask', 'intervention_assignement_id', "asks"),

    }

    _sql_constraints = [
        ('code_uniq', 'unique (code)', '*code* /codeNameUniq')
    ]
intervention_assignement()

class project_work(OpenbaseCore):
    _name = "project.task.work"
    _description = "Task work"
    _inherit = "project.task.work"

    _columns = {
        'manager_id': fields.related('ask_id', 'manager_id', type='many2one', string='Services'),
        'user_id': fields.many2one('res.users', 'Done by', required=False, select="1"),
        'team_id': fields.many2one('openstc.team', 'Done by', required=False, select="1"),
    }

project_work()


class project_task_type(OpenbaseCore):
    _name = "project.task.type"
    _description = "project.task.type"
    _inherit = "project.task.type"

    _columns = {

    }

project_task_type()


class project_task_history(OpenbaseCore):
    _name = 'project.task.history'
    _description = 'History of Tasks'
    _inherit = "project.task.history"

    _columns = {
        'state': fields.selection([('finished', 'Finished'),('absent', 'Absent'),('draft', 'New'),('open', 'In Progress'),('pending', 'Pending'), ('done', 'Done'), ('cancelled', 'Cancelled')], 'State'),

    }

class ask(OpenbaseCore):
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
                                res[id] = ['valid', 'refused', 'to_confirm']

                        if ask['state'] == 'to_confirm' :
                            res[id] = ['valid', 'refused']

                        if ask['state'] == 'refused' :
                            res[id] = ['valid']
                            if isDST == False:
                                res[id] = ['valid', 'to_confirm']

        return res

    def managerOnly(self, cr, uid, record, groups_code):
        return 'DIRE' in groups_code or 'MANA' in groups_code

    _actions = {
        'valid':lambda self,cr,uid,record,groups_code: self.managerOnly(cr,uid,record,groups_code) and record.state in ('wait','to_confirm','refused'),
        'refused':lambda self,cr,uid,record,groups_code: self.managerOnly(cr,uid,record,groups_code) and record.state in ('wait','to_confirm'),
        'to_confirm':lambda self,cr,uid,record,groups_code: 'MANA' in groups_code and record.state in ('wait','refused'),
        }

    def _tooltip(self, cr, uid, ids, myFields, arg, context):
        res = {}

        ask_obj = self.pool.get('openstc.ask')
        project_obj = self.pool.get('project.project')
        task_obj = self.pool.get('project.task')
        user_obj = self.pool.get('res.users')
        modifyBy = ''

        for id in ids:
            res[id] = ''


            ask = ask_obj.browse(cr, uid, id, context)
            if ask :
                if ask.write_uid:
                    modifyBy = user_obj.browse(cr, uid, ask.write_uid.id, context).name
                if ask.state == 'valid' or ask.state == 'finished' :
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

                             if ask.state == 'finished' :
                                 if intervention.state == 'finished' and last_date!=False :
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

                elif ask.state == 'to_confirm' :
                    if ask.note:
                        res[id] = ask.note + '\n('+ modifyBy +')';
                    else:
                        res[id] = _(' request confirmed ')


        return res

    def _get_partner_name(self, cr, uid, ids, fields ,arg, context=None):
        ret = {}.fromkeys(ids,'')
        partner_obj = self.pool.get('res.partner')
        for record in self.browse(cr, uid, ids, context=context):
            if( record.people_name!='' ):
                ret[record.id] = record.people_name
            else :
                ret[record.id] = partner_obj.read(cr, uid, record.partner_id.id,
                                    ['name'],
                                    context)['name']
        return ret


    _columns = {
        'name': fields.char('Asks wording', size=128, required=True, select=True ),
        'create_date' : fields.datetime('Create Date', readonly=True, select=True),
        'create_uid': fields.many2one('res.users', 'Created by', readonly=True),
        'write_uid': fields.many2one('res.users', 'Created by', readonly=True),
        'current_date': fields.datetime('Date'),
        'confirm_by_dst': fields.boolean('Confirm by DST'),
        'description': fields.text('Description', select=True, ),
        'intervention_ids': fields.one2many('project.project', 'ask_id', "Interventions", String="Interventions"),

        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='set null'),
        'partner_name':fields.function(_get_partner_name, method=True, string="PArnter name",type="char", store=True, select=True),

        'partner_address': fields.many2one('res.partner.address', 'Contact',ondelete='set null'),
        'partner_phone': fields.related('partner_address', 'phone', type='char', string='Téléphone'),
        'partner_email': fields.related('partner_address', 'email', type='char', string='Email'),

        'people_name': fields.char('Name', size=128),
        'people_phone': fields.char('Phone', size=10),
        'people_email': fields.char('Email', size=128),

        'intervention_assignement_id':fields.many2one('openstc.intervention.assignement', 'Affectation'),
        'site1': fields.many2one('openstc.site', 'Site principal', required=True, select=True ),
        'site_details': fields.text('Précision sur le site'),
        'note': fields.text('Note'),
        'refusal_reason': fields.text('Refusal reason'),
        'manager_id': fields.many2one('res.users', 'Manager'),
        'partner_service_id': fields.related('partner_id', 'service_id', type='many2one', relation='openstc.service', string='Service du demandeur', help='...'),
        'service_id':fields.many2one('openstc.service', 'Service concerné', select=True),
        'date_deadline': fields.date('Date souhaitée', select=True),
        'state': fields.selection(_get_request_states, 'State', readonly=True,
                          help='If the task is created the state is \'Wait\'.\n If the task is started, the state becomes \'In Progress\'.\n If review is needed the task is in \'Pending\' state.\
                          \n If the task is over, the states is set to \'Done\'.'),

        'tooltip' : fields.function(_tooltip, method=True, string='Tooltip',type='char', store=False),
        'equipment_id': fields.many2one('openstc.equipment','Equipment', select=True),
        'has_equipment': fields.boolean('Request is about equipment'),
        'is_citizen': fields.boolean('Claimer is a citizen'),
    }


    _defaults = {
        'name' : lambda self, cr, uid, context : context['name'] if context and 'name' in context else None,
        'state': '',
        'current_date': lambda *a: datetime.now().strftime('%Y-%m-%d'),
        'actions': [],
        'has_equipment': False,
        'is_citizen': False,
    }


    def create(self, cr, uid, data, context={}):
        data['state'] = 'wait'
        manager_id = self.pool.get('openstc.service').read(cr, uid, data['service_id'],['manager_id'],context)['manager_id']
        if manager_id:
            data['manager_id'] = manager_id[0]

        res = super(ask, self).create(cr, uid, data, context)
        #netsvc.LocalService('workflow').trg_validate(uid, self._name, ids[0], vals['state'], cr)
        #TODO uncomment
        #send_email(self, cr, uid, [res], data, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        isList = isinstance(ids, types.ListType)
        if isList == False :
            ids = [ids]

        #if we validate an ask, we create inter associated and, if needed, task for the inter
        if vals.has_key('state') and vals['state'] == 'valid':
            browse_ask= self.browse(cr, uid, ids[0], context=context)
            #inter with values to create, we use vals data if present
            inter_values = {
                'name': browse_ask.name,
                'date_deadline' : vals['date_deadline'] if vals.has_key('date_deadline') else browse_ask.date_deadline,
                'description': vals['description'] if vals.has_key('description') else browse_ask.description,
                'site1': vals['site1'] if vals.has_key('site1') else browse_ask.site1.id,
                'has_equipment': vals['has_equipment'] if vals.has_key('has_equipment') else browse_ask.has_equipment,
                'equipment_id': vals['equipment_id'] if vals.has_key('equipment_id') else browse_ask.equipment_id and browse_ask.equipment_id.id or False,
                'service_id':  vals['service_id'] if vals.has_key('service_id') else browse_ask.service_id.id
                }

            #pop() fields from vals (because belongs to openstc.task) to use them for creating task
            if vals.pop('create_task',False):
                task_values = {
                   'planned_hours':vals.pop('planned_hours',0.0),
                   'category_id':vals.pop('category_id',False),
                   'name':browse_ask.name
                }
                inter_values.update({'tasks':[(0,0,task_values)]})

            #and we update vals to create inter (and task if needed)
            vals.update({'intervention_ids':[(0,0,inter_values)]})

        res = super(ask, self).write(cr, uid, ids, vals, context=context)
        netsvc.LocalService('workflow').trg_validate(uid, self._name, ids[0], vals['state'], cr)
        #if vals and vals.has_key('email_text'):
            #TODO uncomment
            #send_email(self, cr, uid, ids, vals, context)
        return res



    def action_wait(self, cr, uid, ids):
        self.send_mail(cr, uid, ids, {'state':'wait'})
        return True
    def action_valid(self, cr, uid, ids):
        self.send_mail(cr, uid, ids, {'state':'valid'})
        return True
    def action_confirm(cr, uid, ids):
        #Nothing to do
        return True
    def action_refused( cr, uid, ids):
        #Nothing to do
        return True
    def action_finished(self, cr, uid, ids):
        self.send_mail(cr, uid, ids, {'state':'finished'})
        return True


    def send_mail(self, cr, uid, ids, vals=None, context=None):
        #TODO: check if company wants to send email (info not(opt_out) in partner)
        #We keep only inter if partner have not opt_out checked
        isList = isinstance(ids, types.ListType)
        if isList == False :
            ids = [ids]
        ask = self.browse(cr, uid, ids[0], context=context)
        if not ask.partner_id.opt_out :
            email_obj = self.pool.get("email.template")
            email_tmpl_id = 0
            data_obj = self.pool.get('ir.model.data')
            model_map = {'wait':'openstc_email_template_ask_wait',
                         'valid':'openstc_email_template_ask_valid',
                         'finished':'openstc_email_template_ask_finished'}
            #first, retrieve template_id according to 'state' parameter
            if vals.get('state','') in model_map.keys():
                email_tmpl_id = data_obj.get_object_reference(cr, uid, 'openstc',model_map.get(vals.get('state')))[1]
                if email_tmpl_id:
                    if isinstance(email_tmpl_id, list):
                        email_tmpl_id = email_tmpl_id[0]
                    #generate mail and send it
                    mail_id = email_obj.send_mail(cr, uid, email_tmpl_id, ask.id)
                    self.pool.get("mail.message").write(cr, uid, [mail_id], {})
                    self.pool.get("mail.message").send(cr, uid, [mail_id])

        return True


    def unlink(self, cr, uid, ids, context=None):
        for ask in self.browse(cr, uid, ids):
            if ask.intervention_ids!=None and len(ask.intervention_ids) > 0:
                raise osv.except_osv(_('Suppression Impossible !'),_('Des interventions sont liées à la demande'))
            else:
                return super(ask, self).unlink(cr, uid, ids, context=context)

ask()


#----------------------------------------------------------
# Others
#----------------------------------------------------------

class openstc_planning(OpenbaseCore):
    _name = "openstc.planning"
    _description = "Planning"

    _columns = {
        'name': fields.char('Planning', size=128),
    }

openstc_planning()


class todo(OpenbaseCore):
    _name = "openstc.todo"
    _description = "todo stc"
    _rec_name = "title"

    _columns = {
            'title': fields.char('title', size=128),
            'completed': fields.boolean('Completed'),
    }
todo()