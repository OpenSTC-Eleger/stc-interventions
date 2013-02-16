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
from datetime import datetime,timedelta

from osv import fields, osv
import netsvc

class openstc_pret_checkout_wizard(osv.osv):
    AVAILABLE_STATE_VALUES = [('draft','Brouillon'),('done','Cloturé')]
    _name = "openstc.pret.checkout"
    _rec_name = 'name'
    _columns = {
                'name': fields.related('reservation','name',type='char', string='Réservation Associée', store=True),
                'reservation': fields.many2one('hotel.reservation','Réservation Associée', required=True),
                'date_order': fields.datetime('Date de l\'Etat des lieux', readonly=True),
                'user_id': fields.many2one('res.users', 'Saisie par'),
                'partner_id':fields.related('reservation','partner_id',type='many2one', relation='res.partner', string="Demandeur", store=True),
                'checkout_lines':fields.one2many('openstc.pret.checkout.line', 'checkout_id',string="Ressources empruntées"),
                'state':fields.selection(AVAILABLE_STATE_VALUES, 'Etat', readonly=True),
                'purchase_id':fields.many2one('purchase.order', 'Facture associée', readonly=True),
                #'intervention_id':fields.many2one('openstc.ask', 'Intervention associée'),
            }
    
    _default={
              'state': 'draft',
              }
    
    def default_get(self, cr, uid, fields, context=None):
        ret = super(openstc_pret_checkout_wizard, self).default_get(cr, uid, fields, context)
        if 'reservation_id' in context:
            values = []
            for resa in self.pool.get("hotel.reservation").browse(cr, uid, [context['reservation_id']]):
                ret.update({'reservation':resa.id,
                            'user_id':uid,
                            'state':'draft',
                            'date_order':str(datetime.now())})
                for line in resa.reservation_line:
                    values.append((0,False,{'product_id':line.reserve_product.id,
                                            'qte_reservee':line.qte_reserves}))
            ret.update({'checkout_lines':values})    
        return ret
    
    def create(self, cr, uid, vals,context=None):
        res = super(openstc_pret_checkout_wizard, self).create(cr, uid, vals, context)
        self.pool.get("hotel.reservation").write(cr, uid, [vals['reservation']], {'resa_checkout_id':res}, context=context)
        return res
    
    def open_purchase(self, cr, uid, ids, context=None):
        purchase = self.read(cr, uid, ids[0], ['purchase_id'])
        if purchase['purchase_id']:
            return {
                    'type':'ir.actions.act_window',
                    'view_mode':'form',
                    'target':'new',
                    'res_id':purchase['purchase_id'][0],
                    'res_model':'purchase.order',
                    }
        #En principe, on ne doit jamais arriver jusqu'ici (l'attrs du bouton associé à la méthode doitt l'empêcher)
        return {
                'type':'ir.actions.act_window',
                'view_mode':'form',
                'target':'new',
                'res_model':'purchase.order',
                }
    
    def generer_actions(self, cr, uid, ids, context):
        #TODO: Gérer le cas où des produits n'ont pas le même fournisseur, groupe les produits ayant un fournisseur en commun
        default_location_id = self.pool.get("stock.location").search(cr, uid, [('name','=','Stock')])[0]
        for checkout in self.browse(cr, uid, ids):
            #TODO: Générer actions (interventions)
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'hotel.reservation', checkout.reservation.id, 'done', cr)
            line_values = []
            for line in checkout.checkout_lines:
                if line.etat_retour == 'to_purchase':
                    line_values.append((0,0,{
                                        'product_id':line.product_id.id, 
                                        'product_qty':line.qte_to_purchase, 
                                        'date_planned':str(datetime.now()),
                                        'price_unit':line.product_id.product_tmpl_id.list_price,
                                        'name': line.product_id.name_template,
                                        }))
            #Dans le cas d'une mauvaise manip, si aucun article n'est indiqué comme devant être racheté, on ne fait rien
            if line_values:
                values = {'invoice_method':'manual',
                  'location_id':default_location_id,
                  'partner_id':checkout.partner_id.id,
                  'order_line':line_values,
                  'is_emprunt':False,
                  }
                #On insère les modifs de l'onchange sur partner_id pour compléter les champs obligatoires
                for (key, value) in self.pool.get("purchase.order").onchange_partner_id(cr, uid, False, checkout.partner_id.id)['value'].items():
                    values[key] = value
                purchase_id = self.pool.get("purchase.order").create(cr, uid, values)
                self.write(cr, uid, checkout.id, {'purchase_id':purchase_id})    
            else:
                self.log(cr, uid, checkout.id, ("Aucune facture n'a été créée, car aucun rachat n'est programmé dans l'état des lieux"))
        self.write(cr, uid, ids, {'state':'done'})
        return{'type':'ir.actions.act_window_close'}
    
    def generer_no_actions(self, cr, uid, ids, context):
        for checkout in self.browse(cr, uid, ids):
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'hotel.reservation', checkout.reservation.id, 'done', cr)
            #self.write(cr, uid, ids, {'state':'done'})
        return{'type':'ir.actions.act_window_close'}
        
openstc_pret_checkout_wizard()
AVAILABLE_STATE_TREATMENT_SELECTION = [('draft','Non Planifié'),('in_progress','En cours de Traitement'),('done','Remis en Etat')]
AVAILABLE_ETAT_SELECTION = [('ras','Ne Rien Planifier'),('to_repair','A Réparer'),('to_purchase','A Racheter')]
class openstc_pret_checkout_line_wizard(osv.osv):
    _name = "openstc.pret.checkout.line"
    _columns = {
                'checkout_id':fields.many2one('openstc.pret.checkout','Etat des Lieux'),
                'product_id':fields.many2one('product.product','Article', readonly=True),
                'qte_reservee':fields.integer('Qté prêtée', readonly=True),
                'etat_retour':fields.selection(AVAILABLE_ETAT_SELECTION, 'Etat après utilisation', required=True),
                'state':fields.selection(AVAILABLE_STATE_TREATMENT_SELECTION, 'Avancement', readonly=True),
                'qte_to_purchase':fields.integer('Qté à Racheter'),
                'infos_supp':fields.char('Infos Supplémentaires',size=128),
                'partner_id':fields.related('checkout_id','partner_id', type='many2one',relation='res.partner', string="Emprunteur concerné"),
                'date_order':fields.related('checkout_id','date_order',type='datetime', string='Date Etat des Lieux'),
            }
    _defaults = {
            'state':lambda *a: 'draft',
            }


    def _check_qte_to_purchase(self, cr, uid, ids):
        for line in self.browse(cr, uid, ids):
            if line.qte_to_purchase and line.qte_to_purchase > line.qte_reservee:
                return False
            elif line.qte_to_purchase and line.qte_to_purchase > 0 and line.etat_retour <> 'to_purchase':
                return False
        return True
    
    _constraints = [
                    (_check_qte_to_purchase, "La Qté à Racheter doit-être inférieure à la quantité réservée et n'être renseignée que si l'article doit être racheté", ['qte_reservee','etat_retour','qte_to_purchase'])
                    ]
    
openstc_pret_checkout_line_wizard()

