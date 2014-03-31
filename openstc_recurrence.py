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
from osv import fields, osv

class openstc_task_recurrence(OpenbaseCore):
    _inherit = 'openbase.recurrence'
    _name = 'openstc.task.recurrence'
    
     
    def _get_line_from_occur(self, cr, uid, ids, context=None):
        occ = self.pool.get("project.task").browse(cr, uid, ids, context=context)
        ret = []
        for item in occ:
            if item.recurrence_id.id not in ret:
                ret.append(item.recurrence_id.id)
        return ret
    
    def _get_line_from_inter(self, cr, uid, ids, context=None):
        ret = []
        for inter in self.browse(cr, uid, ids, context=None):
            ret.extend([line.id for line in inter.recurrence_ids])
        return ret
    
    def _get_line_from_contracts(self, cr, uid, ids, context=None):
        ret = []
        for contract in self.browse(cr, uid, ids, context=None):
            ret.extend([line.id for line in contract.contract_line])
        return ret
    
    store_related = {'project.project':[_get_line_from_inter,['equipment_id','site1'],10],
                     'openstc.patrimoine.contract':[_get_line_from_contracts,['equipment_id','site_id','patrimoine_is_equipment'],11],
                    'openstc.task.recurrence':[lambda self,cr,uid,ids,ctx={}:ids,['contract_id'],9]}
    
    """ Instead of using related field, i use functionnal field (because patrimoine module will need this behavior too
    @return: values of 'related' values of fields defined in 'name' params"""
    def related_fields_function(self, cr, uid, ids, name, args, context=None):
        ret = {}.fromkeys(ids, {})
        for recurrence in self.browse(cr, uid, ids, context=context):
            inter = recurrence.intervention_id 
            if recurrence.from_inter and inter:
                val = {
                    'internal_inter':inter.service_id <> False,
                    'technical_service_id':inter.service_id.id if inter.service_id else False,
                    'patrimoine_is_equipment':inter.has_equipment,
                    'site_id':inter.site1.id if inter.site1 else False,
                    'equipment_id':inter.equipment_id.id if inter.equipment_id else False,
                    'date_start':inter.date_start_recurrence,
                    'date_end':inter.date_end_recurrence
                    }
                ret[recurrence.id].update(val)
        return ret
    
    def _related_fields_function(self, cr, uid, ids, name, args, context=None):
        return self.related_fields_function(cr, uid, ids, name, args, context=context)
    
        """ @return: id of the next project.task to Do"""
    def _get_next_task(self, cr, uid, ids, name, args, context=None):
        ret = {}.fromkeys(ids, False)
        task_obj = self.pool.get('project.task')
        for recurrence in self.browse(cr, uid, ids, context=context):
            task_ids = task_obj.search(cr, uid, [('state','not in',('done','cancelled','absent')),('recurrence_id.id','=',recurrence.id)], order='date_start,date_deadline', context=context)
            if task_ids:
                ret[recurrence.id] = task_ids[0]
        return ret
    
    _columns = {
        'recurrence':fields.boolean('has recurrence'),
        'from_inter':fields.boolean('From intervention'),
        'name':fields.char('Name',size=128, required=True),
        'is_team':fields.boolean('Is Team Work'),
        'agent_id':fields.many2one('res.users', 'Agent'),
        'team_id':fields.many2one('openstc.team', 'Team'),
        'task_categ_id':fields.many2one('openstc.task.category', 'Task category'),
        'planned_hours':fields.float('Planned hours'),
        'supplier_cost':fields.float('Supplier Cost'),
        
        'next_task':fields.function(_get_next_task, method=True, type='many2one', relation="project.task", string='next task of the recurrence', help="Date of the next task to do in this contract",
                                     store=False),
        
        'internal_inter':fields.function(_related_fields_function, multi="related_recur",type='boolean', string='Internal Intervention', store=store_related),
        'technical_service_id':fields.function(_related_fields_function, multi="related_recur",type='many2one',relation='openstc.service', string='Internal Service', store=store_related),
        'equipment_id':fields.function(_related_fields_function, multi="related_recur",type='many2one',relation='openstc.equipment',string="equipment", store=store_related),
        'site_id':fields.function(_related_fields_function, multi="related_recur",type='many2one',relation='openstc.site',string="Site", store=store_related),
        'patrimoine_is_equipment':fields.function(_related_fields_function, multi="related_recur",type='boolean',string='Is Equipment',store=store_related),
        'patrimoine_name':fields.function(_related_fields_function, multi="related_recur",type='char', string="patrimony", store=store_related),
        
        'date_start':fields.function(_related_fields_function, multi="related_recur",type='datetime', string="Date Start", store=store_related),
        'date_end':fields.function(_related_fields_function, multi="related_recur",type='datetime', string="Date Start", store=store_related),        
        'date_start_recurrence':fields.datetime('Date start (out from a contract)'),
        'date_end_recurrence':fields.datetime('Date start (out from a contract)'),
        
        'occurrence_ids':fields.one2many('project.task','recurrence_id', 'Tasks'),
        'intervention_id':fields.many2one('project.project', 'Intervention'),
        }
    _defaults = {
        'recur_length_type':lambda *a:'until',
        'recurrence': lambda *a: False,
        'recur_month_type':'monthday',
        'is_team': lambda *a: False,
        'from_inter': lambda *a: True,
        }
    
    _order = "next_inter,technical_service_id"
    
    """
    @param record: browse_record object of contract.line to generate tasks
    @param date: datetime object representing date_start of the task to be created after this method
    @return: data used to create tasks
    @note: this method override the one created in openbase.recurrence to customize behavior"""
    def prepare_occurrences(self, cr, uid, record, date, context=None):
        
        val = super(openstc_task_recurrence, self).prepare_occurrences(cr, uid, record, date, context=context)
        #assert record.contract_id.intervention_id, 'Error: intervention_id (project.project) is not present on contract %s :%s' % (str(record.contract_id.id),record.contract_id.name)
        return {
            'name':record.name,
            'recurrence_id':val.get('recurrence_id'),
            'date_deadline':val.get('date_start'),
            #'project_id':record.contract_id.intervention_id.id,
            'user_id':record.agent_id.id if not record.is_team else False,
            'team_id':record.team_id.id if record.is_team else False,
            'planned_hours': record.planned_hours
            
            }
    
openstc_task_recurrence()

class intervention(OpenbaseCore):
    
    _inherit = "project.project"
    
    """ @return: list of ids of project.task considered as 'TODO'
    TODO tasks are all the task not coming from recurrence,
    and all the next tasks of each recurrence"""
    def _get_tasks_todo(self, cr, uid, ids, name, args, context=None):
        ret = {}.fromkeys(ids, [])
        for inter in self.browse(cr, uid, ids, context=context):
            val = [task.id for task in inter.tasks]
            for recurrence in inter.recurrence_ids:
                recur_task = recurrence.next_task
                if recur_task:
                    val.append(recur_task.id)
            ret[inter.id] = val
        return ret
    
    _columns = {
        'recurrence_ids':fields.one2many('openstc.task.recurrence', 'intervention_id', 'Recurrence(s)'),
        'todo_tasks':fields.function(_get_tasks_todo, method=True, type='char', string="Tasks todo", store=False),
        }

intervention()

class task(OpenbaseCore):
    
    _inherit = "project.task"
    _columns = {
        'recurrence_id':fields.many2one('openstc.task.recurrence', 'Contract Line', ondelete="cascade"),
        }
task()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: