# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################
from osv import fields, osv
import time
import netsvc
from mx import DateTime
import datetime
from tools import config
from tools.translate import _

class hotel_folio(osv.osv):
    
    _inherit = "hotel.folio"
    _name = "hotel.folio"

    def copy(self, cr, uid, id, default=None,context={}):
        order_id = self.browse(cr, uid, id, context).order_id.id
        return  self.pool.get('sale.order').copy(cr, uid, order_id, default=None,context={})
    
    def _invoiced(self, cursor, user, ids, name, arg, context=None):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids, context)]
        return  self.pool.get('sale.order')._invoiced(cursor, user, order_ids, name, arg, context=None)

    #TOCHECK: does obj has to be replaced by obj.order_id ?
    def _invoiced_search(self, cursor, user, obj, name, args):
        return  self.pool.get('sale.order')._invoiced_search(cursor, user, obj, name, args)
    
    def _amount_untaxed(self, cr, uid, ids, field_name, arg, context):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids, context)]
        return self.pool.get('sale.order')._amount_untaxed(cr, uid, order_ids, field_name, arg, context)
    
    def _amount_tax(self, cr, uid, ids, field_name, arg, context):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids, context)]
        return self.pool.get('sale.order')._amount_tax(cr, uid, order_ids, field_name, arg, context)
    
    def _amount_total(self, cr, uid, ids, field_name, arg, context):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids, context)]
        return self.pool.get('sale.order')._amount_total(cr, uid, order_ids, field_name, arg, context)
    
    def onchange_dates(self,cr,uid,ids,checkin_date=False,checkout_date=False,duration=False):
        value = {}
        if not duration:
            duration = 0
            if checkin_date and checkout_date:
                chkin_dt = datetime.datetime.strptime(checkin_date,'%Y-%m-%d %H:%M:%S')
                chkout_dt = datetime.datetime.strptime(checkout_date,'%Y-%m-%d %H:%M:%S') 
                dur = chkout_dt - chkin_dt
                duration = dur.days
            value.update({'value':{'duration':duration}})
        else:
            if checkin_date:
                chkin_dt = datetime.datetime.strptime(checkin_date,'%Y-%m-%d %H:%M:%S')
                chkout_dt = chkin_dt + datetime.timedelta(days=duration)
                checkout_date = datetime.datetime.strftime(chkout_dt,'%Y-%m-%d %H:%M:%S')
                value.update({'value':{'checkout_date':checkout_date}})
        return value
    
    def create(self, cr, uid, vals, context=None, check=True):
        tmp_room_lines = vals.get('room_lines',[])
        tmp_service_lines = vals.get('service_lines',[])
        vals['order_policy'] = vals.get('hotel_policy','manual')
        if not vals.has_key("folio_id"):
            vals.update({'room_lines':[],'service_lines':[]})
            folio_id = super(hotel_folio, self).create(cr, uid, vals, context)
            for line in tmp_room_lines:
                line[2].update({'folio_id':folio_id})
            for line in tmp_service_lines:
                line[2].update({'folio_id':folio_id})
            vals.update({'room_lines':tmp_room_lines,'service_lines':tmp_service_lines})
            super(hotel_folio, self).write(cr, uid,[folio_id], vals, context)
        else:
            folio_id = super(hotel_folio, self).create(cr, uid, vals, context)
        return folio_id
    
   
    def onchange_shop_id(self, cr, uid, ids, shop_id):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids)]
        return  self.pool.get('sale.order').onchange_shop_id(cr, uid, order_ids, shop_id)
    
    def onchange_partner_id(self, cr, uid, ids, part):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids)]
        return  self.pool.get('sale.order').onchange_partner_id(cr, uid, order_ids, part)
    
    def button_dummy(self, cr, uid, ids, context={}):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids, context)]
        return  self.pool.get('sale.order').button_dummy(cr, uid, order_ids, context={})
    
    def action_invoice_create(self, cr, uid, ids, grouped=False, states=['confirmed','done']):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids)]
        i = self.pool.get('sale.order').action_invoice_create(cr, uid, order_ids, grouped=False, states=['confirmed','done'])
        for line in self.browse(cr, uid, ids, context={}):
            self.write(cr, uid, [line.id], {'invoiced':True})
            if grouped:
               self.write(cr, uid, [line.id], {'state' : 'progress'})
            else:
               self.write(cr, uid, [line.id], {'state' : 'progress'})
        return i 

   
    def action_invoice_cancel(self, cr, uid, ids, context={}):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids, context)]
        res = self.pool.get('sale.order').action_invoice_cancel(cr, uid, order_ids, context={})
        for sale in self.browse(cr, uid, ids):
            for line in sale.order_line:
                self.pool.get('sale.order.line').write(cr, uid, [line.id], {'invoiced': invoiced})
        self.write(cr, uid, ids, {'state':'invoice_except', 'invoice_id':False})
        return res  
    def action_cancel(self, cr, uid, ids, context={}):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids, context)]
        c = self.pool.get('sale.order').action_cancel(cr, uid, order_ids, context={})
        ok = True
        for sale in self.browse(cr, uid, ids):
            for r in self.read(cr,uid,ids,['picking_ids']):
                for pick in r['picking_ids']:
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'stock.picking', pick, 'button_cancel', cr)
            for r in self.read(cr,uid,ids,['invoice_ids']):
                for inv in r['invoice_ids']:
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'account.invoice', inv, 'invoice_cancel', cr)
            
        self.write(cr,uid,ids,{'state':'cancel'})
        return c
    
    def action_wait(self, cr, uid, ids, *args):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids)]
        res = self.pool.get('sale.order').action_wait(cr, uid, order_ids, *args)
        for o in self.browse(cr, uid, ids):
            if (o.order_policy == 'manual') and (not o.invoice_ids):
                self.write(cr, uid, [o.id], {'state': 'manual'})
            else:
                self.write(cr, uid, [o.id], {'state': 'progress'})
        return res
    def test_state(self, cr, uid, ids, mode, *args):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids)]
        write_done_ids = []
        write_cancel_ids = []
        res = self.pool.get('sale.order').test_state(cr, uid, order_ids, mode, *args)
        if write_done_ids:
            self.pool.get('sale.order.line').write(cr, uid, write_done_ids, {'state': 'done'})
        if write_cancel_ids:
            self.pool.get('sale.order.line').write(cr, uid, write_cancel_ids, {'state': 'cancel'})
        return res 
    def procurement_lines_get(self, cr, uid, ids, *args):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids)]
        res = self.pool.get('sale.order').procurement_lines_get(cr, uid, order_ids, *args)
        return  res
    def action_ship_create(self, cr, uid, ids, *args):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids)]
        res =  self.pool.get('sale.order').action_ship_create(cr, uid, order_ids, *args)
        return res
    def action_ship_end(self, cr, uid, ids, context={}):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids, context)]
        res = self.pool.get('sale.order').action_ship_end(cr, uid, order_ids, context={})
        for order in self.browse(cr, uid, ids):
            val = {'shipped':True}
            self.write(cr, uid, [order.id], val)
        return res 
    def _log_event(self, cr, uid, ids, factor=0.7, name='Open Order'):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids)]
        return  self.pool.get('sale.order')._log_event(cr, uid, order_ids, factor=0.7, name='Open Order')
    def has_stockable_products(self,cr, uid, ids, *args):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids)]
        return  self.pool.get('sale.order').has_stockable_products(cr, uid, order_ids, *args)
    def action_cancel_draft(self, cr, uid, ids, *args):
        order_ids = [x.order_id.id for x in self.browse(cr, uid, ids)]
        d = self.pool.get('sale.order').action_cancel_draft(cr, uid, order_ids, *args)
        self.write(cr, uid, ids, {'state':'draft', 'invoice_ids':[], 'shipped':0})
        self.pool.get('sale.order.line').write(cr, uid,ids, {'invoiced':False, 'state':'draft', 'invoice_lines':[(6,0,[])]})
        return d
  
hotel_folio()
