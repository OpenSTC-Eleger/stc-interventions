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

import openstc

def _get_request_states(self, cursor, user_id, context=None):
    return (
                ('wait', 'Wait'),('to_confirm', 'To be confirm'),('valid', 'Valid'),('refused', 'Refused'),('finished', 'Finished')
            )


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""" Ask or Intervention request """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class ask(OpenbaseCore):
    _name = "openstc.ask"
    _description = "openstc.ask"
    _order = "create_date desc"


    """
        Mail templates
    """
    def _mail_templates(self, cr, uid, context=None):
        return  {'wait':'openstc_email_template_ask_wait',
                 'valid':'openstc_email_template_ask_valid',
                 'cancelled':'openstc_email_template_ask_cancelled',
                 'finished':'openstc_email_template_ask_finished'}

    def _get_user_service(self, cr, uid, ipurchase_orderds, fieldnames, name, args):
        return False


    def _get_uid(self, cr, uid, context=None):
        return uid

    def _get_services(self, cr, uid, context=None):
        user_obj = self.pool.get('res.users')
        return user_obj.read(cr, uid, uid, ['service_ids'],context)['service_ids']


    def managerOnly(self, cr, uid, record, groups_code):
        return 'DIRE' in groups_code or 'MANA' in groups_code

    _actions = {
        'valid':lambda self,cr,uid,record,groups_code: self.managerOnly(cr,uid,record,groups_code) and record.state in ('wait','to_confirm','refused') and
                    self.pool.get("res.users").search(cr, uid,['&',('id', '=', uid ),('service_ids','in',record.service_id.id)]),
        'refused':lambda self,cr,uid,record,groups_code: self.managerOnly(cr,uid,record,groups_code) and record.state in ('wait','to_confirm') and
                    self.pool.get("res.users").search(cr, uid,['&',('id', '=', uid ),('service_ids','in',record.service_id.id)]),
        'to_confirm':lambda self,cr,uid,record,groups_code: 'MANA' in groups_code and record.state in ('wait','refused') and
                    self.pool.get("res.users").search(cr, uid,['&',('id', '=', uid ),('service_ids','in',record.service_id.id)]),
        }


    """
    build tooltip on ask
    """
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


    """
    Add partner name information on ask
    """
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
        return res


    """
    Test if send mail after action on ask
    @param vals: contains state
    @return: return True if current ask meets conditions to send email
    """
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
        if vals.has_key('state') :
            netsvc.LocalService('workflow').trg_validate(uid, self._name, ids[0], vals['state'], cr)
        return res


    """ Workflow actions"""""""""""""""""""""""""""""""""""""""""""""""""""""""
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def action_wait(self, cr, uid, ids):
        self.valid_and_send_mail(cr, uid, ids,{'state':'wait'})
        return True
    def action_valid(self, cr, uid, ids):
        self.valid_and_send_mail(cr, uid, ids,{'state':'valid'})
        return True
    def action_confirm(self, cr, uid, ids):
        #Nothing to do
        return True
    def action_refused(self, cr, uid, ids):
        self.valid_and_send_mail(cr, uid, ids,{'state':'cancelled'})
        return True
    def action_finished(self, cr, uid, ids):
        self.valid_and_send_mail(cr, uid, ids,{'state':'finished'})
        return True


    """
    Test if send mail after action on ask
    @param vals: contains state
    @return: return True if current ask meets conditions to send email
    """
    def valid_and_send_mail(self, cr, uid, ids, vals, context=None):
        ask = self.browse(cr, uid, ids[0], context=context)
        try:
            #sending mail if partner's type has option 'sending mail'
            if ask.partner_id.type_id.sending_mail:
                 self.send_mail(cr, uid, ask.id, vals, 'openstc', self._name,
                                    self._mail_templates(cr, uid, context))
        #Except if type is not defined on partner (normaly not possible)
        except Exception,e:
            return False
        return True

    """
    delete ask is not possible if ask has some interventions
    """
    def unlink(self, cr, uid, ids, context=None):
        for ask in self.browse(cr, uid, ids):
            if ask.intervention_ids!=None and len(ask.intervention_ids) > 0:
                raise osv.except_osv(_('Suppression Impossible !'),_('Des interventions sont liées à la demande'))
            else:
                return super(ask, self).unlink(cr, uid, ids, context=context)

ask()