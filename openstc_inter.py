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


from openbase.openbase_core import OpenbaseCore


import netsvc
import pytz
from osv.orm import browse_record, browse_null
from osv import fields, osv, orm
from datetime import datetime, timedelta
from dateutil import *
from dateutil.tz import *

from tools.translate import _

import openstc

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" Interventions """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class project(OpenbaseCore):
    _name = "project.project"
    _description = "Interventon stc"
    _inherit = "project.project"


    """
        Mail templates
    """
    def _mail_templates(self, cr, uid, context=None):
        return  {'scheduled':'openstc_email_template_project_scheduled'}

    def _complete_name(self, cr, uid, ids, name, args, context=None):
        return super(project, self)._complete_name(cr, uid, ids, name, args, context=context)

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

    """
    build tooltip information
    """
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
        'complete_name': fields.function(_complete_name, string="Project Name", type='char', size=250, store=True),
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
        if vals.has_key('state') :
            netsvc.LocalService('workflow').trg_validate(uid, self._name, ids[0], vals['state'], cr)
        return res


    """ Workflow actions"""""""""""""""""""""""""""""""""""""""""""""""""""""""
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def action_open(self, cr, uid, ids):
        return True

    def action_template(self, cr, uid, ids):
        return True

    def action_scheduled(self, cr, uid, ids):
        self.valid_and_send_mail(cr, uid, ids,{'state':'scheduled'})
        return True

    def action_pending(self, cr, uid, ids):
        return True

    def action_cancelled(self, cr, uid, ids):
        return True

    def action_finished(self, cr, uid, ids):
        return True


    """
    Test if send mail after action on ask
    @param vals: contains state
    @return: return True if current ask meets conditions to send email
    """
    def valid_and_send_mail(self, cr, uid, ids, vals, context=None):
        inter = self.browse(cr, uid, ids[0], context=context)
        send_mail = False
        if inter.ask_id.people_email != '':
            send_mail=True
        elif inter.ask_id.partner_id and inter.ask_id.partner_id.type_id :
            if inter.ask_id.partner_id.type_id.sending_mail :
                send_mail=True
        if not send_mail: return False

        try:
             self.send_mail(cr, uid, inter.id, vals, 'openstc', self._name,
                                self._mail_templates(cr, uid, context))
        #Except if type is not defined on partner, or ask has no partner (normaly not possible)
        except Exception,e:
            return False
        return True


    #Cancel intervention from swif
    def cancel(self, cr, uid, ids, params, context=None):
        #print("test"+params)
        project_obj = self.pool.get(self._name)
        project = project_obj.browse(cr, uid, ids[0], context)
        task_obj = self.pool.get('project.task')
        ask_obj = self.pool.get('openstc.ask')

        #update intervention's tasks
        if openstc._test_params(params, ['state','cancel_reason'])!= False:
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
        return True;

    _defaults = {
        'ask_id' : _get_ask,
        'has_equipment': False,
    }

    _sql_constraints = [
        ('ask_uniq', 'unique(name,ask_id)', 'Demande déjà validée!'),
    ]


project()


class intervention_assignement(osv.osv):
    _name = "openstc.intervention.assignement"
    _description = ""

    _actions = {
        'create':lambda self,cr,uid,record, groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,
        'update':lambda self,cr,uid,record, groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,
        'delete':lambda self,cr,uid,record, groups_code: 'DIRE' in groups_code,

        }
    def _get_actions(self, cr, uid, ids, myFields ,arg, context=None):
        #default value: empty string for each id
        ret = {}.fromkeys(ids,'')
        groups_code = []
        groups_code = [group.code for group in self.pool.get("res.users").browse(cr, uid, uid, context=context).groups_id if group.code]

        #evaluation of each _actions item, if test returns True, adds key to actions possible for this record
        for record in self.browse(cr, uid, ids, context=context):
            #ret.update({inter['id']:','.join([key for key,func in self._actions.items() if func(self,cr,uid,inter)])})
            ret.update({record.id:[key for key,func in self._actions.items() if func(self,cr,uid,record,groups_code)]})
        return ret


    _columns = {
            'name': fields.char('Affectation ', size=128, required=True),
            'code': fields.char('Code affectation', size=32, required=True),
            'asksAssigned': fields.one2many('openstc.ask', 'intervention_assignement_id', "asks"),
            'actions':fields.function(_get_actions, method=True, string="Actions possibles",type="char", store=False),

    }

    _sql_constraints = [
        ('code_uniq', 'unique (code)', '*code* / The code name must be unique !')
    ]
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
                                 if intervention.state == 'closed' and last_date!=False :
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
        'name': fields.char('Asks wording', size=128, required=True, select=True),
        'create_date' : fields.datetime('Create Date', readonly=True, select=False),
        'create_uid': fields.many2one('res.users', 'Created by', readonly=True),
        'write_uid': fields.many2one('res.users', 'Created by', readonly=True),
        'current_date': fields.datetime('Date'),
        'confirm_by_dst': fields.boolean('Confirm by DST'),
        'description': fields.text('Description'),
        'intervention_ids': fields.one2many('project.project', 'ask_id', "Interventions", String="Interventions"),

        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='set null'),
        'partner_name':fields.function(_get_partner_name, method=True, string="PArnter name",type="char", store=True),
        'partner_address': fields.many2one('res.partner.address', 'Contact',ondelete='set null'),

        'partner_type': fields.related('partner_id', 'type_id', string='Partner type', type='many2one', relation='openstc.partner.type'),
#        'partner_type': fields.many2one('openstc.partner.type', 'Partner Type', required=False),
#        'partner_type_code': fields.char('Partner code', size=128),

        'partner_phone': fields.related('partner_address', 'phone', type='char', string='Téléphone'),
        'partner_email': fields.related('partner_address', 'email', type='char', string='Email'),

        'people_name': fields.char('Name', size=128),
        'people_phone': fields.char('Phone', size=10),
        'people_email': fields.char('Email', size=128),

        'intervention_assignement_id':fields.many2one('openstc.intervention.assignement', 'Affectation'),
        'site1': fields.many2one('openstc.site', 'Site principal', required=True),
#        'site_name': fields.related('site1', 'name', type='char', string='Site'),
#        'site2': fields.many2one('openstc.site', 'Site secondaire'),
#        'site3': fields.many2one('openstc.site', 'Place'),
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
        'equipment_id': fields.many2one('openstc.equipment','Equipment'),
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

    def getNbRequestsTodo(self, cr, uid, users_id, filter=[], context=None):
        if not isinstance(users_id, list):
            users_id = [users_id]
        ret = {}
        for user in self.pool.get("res.users").browse(cr, uid, users_id, context=context):
            ret.update({str(user.id):0})
            #first, i get the code of user groups to filter easier
            groups = [group.code for group in user.groups_id if group.code]
            search_filter = []
            if 'DIRE' in groups:
                search_filter.extend([('state','=','confirm')])
            elif 'MANA' in groups:
                search_filter.extend([('state','=','wait')])
            #NOTE: if user is not DST nor Manager, returns all requests

            #launch search_count method adding optionnal filter defined in UI
            search_filter.extend(filter)
            ret[str(user.id)] = self.search_count(cr, user.id, search_filter, context=context)
        return ret


ask()


project()
