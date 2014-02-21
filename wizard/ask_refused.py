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

from osv import osv
from osv import fields
from tools.translate import _

class CreateAskMemory(osv.osv_memory):
    _name = 'openstc.refused.ask.wizard'
    _description = 'ask'

    _columns = {
        'ask_id': fields.many2one('openstc.ask', 'Ask', help='Select a ask to'),
        'state': fields.related('ask_id', 'state', type='boolean'),
        'refusal_reason' : fields.text('Raison de refus'),
        'note': fields.text('Note'),
        'qualifier_id': fields.many2one('res.users', 'Qualififier'),
    }

    def _get_active_ask(self, cr, uid, context=None):

        if context is None:
            return False
        else:
            return context.get('active_id', False)



    _defaults = {
        'ask_id': _get_active_ask,
    }

    def _action_open_window(self, cr, uid, data, context):
        """
        This function gets default values
        """
        res = super(CreateAskMemory, self).default_get(cr, uid, fields, context=context)
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False) or False
        if not record_id:
            return res
        else:
            ask_obj = self.pool.get('openstc.ask')
            asks = ask_obj.browse(cr, uid, [record_id], context=context)
            if asks[0] != None and asks[0].id != 0 and asks[0].state == 'valid':
                return res
            else:
                raise osv.except_osv(_('Warning !'),_("There is no valid ask selected !") )
        return res


    def action_refused_ask(self, cr, uid, ids, context=None):

        this = self.browse(cr, uid, ids[0], context=context)
        ask_obj = self.pool.get('openstc.ask')
        if len(context.get('active_ids')) > 1:
            ask_ids = context.get('active_ids')
        else:
            ask_ids = [this.ask_id.id]

        modified = False
        for id in ask_ids:
            asks = ask_obj.browse(cr, uid, [id], context=context)
            if asks[0] != None and asks[0].id != 0 : #and asks[0].state == 'valid':
                ask_obj.write(cr, uid, [asks[0].id], {
                        'refusal_reason': this.refusal_reason or 'A completer',
                        'state': 'refused',
                        'note': this.note,
                        'qualifier_id': uid,
                        }, context=context)
                modified = True

        if not modified:
             raise osv.except_osv(_('Warning !'),_("There is no valid ask selected !") )


        return {'type': 'ir.actions.act_window_close'}

CreateAskMemory()