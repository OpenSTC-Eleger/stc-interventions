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

#comment

from osv import fields, osv
from tools.translate import _

class ModifyService(osv.osv_memory):
    _name="openstc.modify.ask.service.wizard"
    _description = 'Modify ask'

    _columns = {
        'ask_id': fields.many2one('openstc.ask', 'Ask'),
        'name': fields.char('Name', size=128, readonly=True),
        'service_id': fields.many2one('openstc.service', 'Service'),
    }

    def _get_active_ask(self, cr, uid, context=None):
        if context is None:
            return False
        else:
            return context.get('active_id', False)

    def _get_ask_name(self, cr, uid, context=None):
        ask_id = self._get_active_ask(cr, uid, context)
        if ask_id :
            return self.pool.get('openstc.ask').read(cr, uid, ask_id,['name'],context)['name']
        return False

    def _get_service(self, cr, uid, context=None):
        ask_id = self._get_active_ask(cr, uid, context)
        if ask_id :
            service_id = self.pool.get('openstc.ask').read(cr, uid, ask_id,['service_id'],context)['service_id']
            if service_id :
                return service_id[0]
        return False

    _defaults = {
        'ask_id': _get_active_ask,
        'name': _get_ask_name,
        'service_id': _get_service,
    }


    def modify_service(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids[0], context=context)
        ask_obj = self.pool.get('openstc.ask')
        ask_obj.write(cr, uid, [this.ask_id.id], {
                    'service_id': this.service_id.id,
            }, context=context)

        return {'type': 'ir.actions.act_window_close'}


ModifyService()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

