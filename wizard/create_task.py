# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenAcademy module for OpenERP, Courses management
#    Copyright (C) 2012 L'Heureux Cyclage (<http://www.heureux-cyclage.org>) Ludovic CHEVALIER
#
#    This file is a part of OpenAcademy
#
#    OpenAcademy is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    OpenAcademy is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from osv import fields
from tools.translate import _

SERVICE = None

def setSERVICE(service):
    global SERVICE
    SERVICE = service

class CreateTaskMemory(osv.osv_memory):
    _name = 'openstc.create.task.wizard'
    _description = 'Link task to ask'

    _columns = {
        'inter_id': fields.many2one('project.project', 'Intervention', help='Select an intervention to'),
        'ask_id': fields.many2one('openstc.ask', 'Ask'),
        'inter_state': fields.related('inter_id', 'state', type='boolean'),
        'inter_name': fields.char('Name', size=128, readonly=True),
        'inter_date_deadline': fields.date('Deadline', readonly=True),
        'inter_manager' : fields.many2one('res.users', 'Manager'),
        'inter_service_id': fields.many2one('openstc.service', 'Service', readonly=True),
        'inter_site1': fields.many2one('openstc.site', 'Site principal', readonly=True),
        'task_ids': fields.one2many('openstc.task.memory', 'wizard_id', 'Tasks', help='Tasks for this ask'),
    }

    def _get_active_inter(self, cr, uid, context=None):
        if context is None:
            return False
        else:
            return context.get('active_id', False)

    def _get_active_ask(self, cr, uid, context=None):
        inter_id = self._get_active_inter(cr, uid, context)
        if inter_id:
            ask_id = self.pool.get('project.project').read(cr, uid, inter_id,['ask_id'],context)['ask_id']
            if ask_id :
                return ask_id[0]
        return False


    def _get_state_inter(self, cr, uid, context=None):
        inter_id = self._get_active_inter(cr, uid, context)
        if inter_id:
            return self.pool.get('project.project').read(cr, uid, inter_id,['state'],context)['state']
        else:
             return False

    def _get_name_inter(self, cr, uid, context=None):
        inter_id = self._get_active_inter(cr, uid, context)
        if inter_id:
            return self.pool.get('project.project').read(cr, uid, inter_id,['name'],context)['name']
        else:
            return False

    def _get_date_deadline_inter(self, cr, uid, context=None):
        inter_id = self._get_active_inter(cr, uid, context)
        if inter_id:
            return self.pool.get('project.project').read(cr, uid, inter_id,['date_deadline'],context)['date_deadline']
        else:
             return False

    def _get_site1_inter(self, cr, uid, context=None):
        inter_id = self._get_active_inter(cr, uid, context)
        if inter_id :
            site_id = self.pool.get('project.project').read(cr, uid, inter_id,['site1'],context)['site1']
            if site_id :
                return site_id[0]
        return False

    def _get_service_inter(self, cr, uid, context=None):
        ask_id = self._get_active_ask(cr, uid, context)
        if ask_id :
            service_id = self.pool.get('openstc.ask').read(cr, uid, ask_id,['service_id'],context)['service_id']
            if service_id :
                setSERVICE(service_id[0])
                return service_id[0]
        return False


    def fields_get(self, cr, uid, fields=None, context=None):
        self._get_service_inter(cr, uid, context)
        return super(CreateTaskMemory, self).fields_get(cr, uid, fields, context)


    _defaults = {
        'inter_id': _get_active_inter,
        'ask_id': _get_active_ask,
        'inter_state' : _get_state_inter,
        'inter_date_deadline':  _get_date_deadline_inter,
        'inter_name':  _get_name_inter,
        'inter_site1':  _get_site1_inter,
        'inter_service_id': _get_service_inter,
    }

    def action_add_task(self, cr, uid, ids, context=None):

        this = self.browse(cr, uid, ids[0], context=context)
        ask_obj = self.pool.get('openstc.ask')
        inter_obj = self.pool.get('project.project')
        task_obj = self.pool.get('project.task')
        task_work_obj = self.pool.get('project.task.work')
        created = False

        #TODO : Y'a t-il un état state = 'running'
        ask_obj.write(cr, uid, [this.ask_id.id], {
                    'manager_id': uid,
            }, context=context)




        if this != None :
            compagny_id = None

            for task in this.task_ids:
                if task.user_id :
                    compagny = task.user_id.company_id
                    if compagny:
                        compagny_id = compagny.id


                task_id = task_obj.create(cr, uid, {
                    'name': task.name or 'A completer',
                    'project_id': this.inter_id.id or False,
                    'planned_hours': task.planned_hours or False,
                    'state': 'open',
                    'date_deadline': this.inter_date_deadline or False,
                    'dst_group_id': 18,
                    'user_id': task.user_id.id or False,
                    'category_id': task.category_id.id or False,
                    'ask_id': this.ask_id.id or False,
                }, context=context)
                task_work_obj.create(cr, uid, {
                    'name': task.name or 'A completer',
                    'task_id': task_id or False,
                    'hours': 0,
                    'user_id': task.user_id.id or False,
                    'company_id': compagny_id or False,
                }, context=context)
                created= True

        if not created:
             raise osv.except_osv(_('Warning !'),_("There is no valid ask selected !") )


        return {'type': 'ir.actions.act_window_close'}

CreateTaskMemory()


class TaskMemory(osv.osv_memory):
    _name = 'openstc.task.memory'
    _description = 'Task management'

    def fields_get(self, cr, uid, fields=None, context=None):
        res = super(TaskMemory, self).fields_get(cr, uid, fields, context)
        for field in res:
            if field == "category_id":
                res[field]['domain']=[('service_ids','in',[SERVICE])]
        return res

    _columns = {
        'name': fields.char('Name', size=64, help='Help note', required=True),
        'user_id':fields.many2one('res.users', 'Assigned to'),
        'planned_hours': fields.float('Planned Hours', help='Estimated time to do the task, usually set by the project manager when the task is in draft state.'),
        'wizard_id': fields.many2one('openstc.create.task.wizard', 'Wizard', help='Help note'),
        'category_id': fields.many2one('openstc.task.category', 'Category', help='...'),#, domain=[('service_ids', 'in', [SERVICE])]
    }

    def _check_time(self, cr, uid, ids, context=None):
        tasks = self.browse(cr, uid, ids, context=context)
        check = True
        for task in tasks:
            if task.planned_hours < 0:
                check = False
        return check


    _constraints = [
        (_check_time, 'Error: Invalid Time', ['planned_hours', 'Incorrect Time']),
    ]

TaskMemory()






# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
