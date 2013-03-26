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
from tools.translate import _
from mx.DateTime.mxDateTime import strptime
import time
import base64
import unicodedata
import re
import pytz

#----------------------------------------------------------
# Fournitures
#----------------------------------------------------------
class product_product(osv.osv):

    def _calc_qte_dispo_now(self, cr, uid, ids, name, args, context=None):
        print("début calcul qté dispo now")
        cr.execute("""select hrl.reserve_product as prod_id, sum(hrl.qte_reserves) as qte_reserves
        from hotel_reservation as hr, hotel_reservation_line as hrl
        where hr.id = hrl.line_id
        and hrl.reserve_product in %s
        and hr.state in ('draft','confirm','in_use')
        group by hrl.reserve_product;""", (tuple(ids),))
        list_prod_reserved = cr.fetchall()
        stock_prod = self._product_available(cr, uid, ids, ['virtual_available'])
        ret = {}
        #Par défaut, on indique la qté max pour chaque produit
        for id in ids:
            ret[id] = stock_prod[id]['virtual_available']
        #Puis pour les articles réservés, on en retranche le nombre réservés
        for prod in list_prod_reserved:
            ret[prod[0]] -= prod[1]
        print(ret)
        return ret

    AVAILABLE_ETATS = (("neuf", "Neuf"), ("bon", "Bon"), ("moyen", "Moyen"), ("mauvais", "Mauvais"), ("inutilisable", "Inutilisable"))

    _name = "product.product"
    _inherit = "product.product"
    _description = "Produit"
    
    #Method to override in order to add some products type and being able to filter product.product according to work context (internvetions, resa etc...)
    def return_type_prod_values(self, cr, uid, context=None):
        return [('ressource','Ressource Réservable'),('materiel','Matériel pour Intervention')]
    
    def _get_type_prod_values(self, cr, uid, context=None):
        return self.return_type_prod_values(cr, uid, context)
    
    _columns = {
        "qte_dispo": fields.function(_calc_qte_dispo_now, method=True, string="Disponible Aujourd'hui", type="integer"),
        "etat": fields.selection(AVAILABLE_ETATS, "Etat"),
        "seuil_confirm":fields.integer("Qté Max sans Validation", help="Qté Maximale avant laquelle une étape de validation par un responsable est nécessaire"),
        "bloquant":fields.boolean("\"Non disponibilité\" bloquante", help="Un produit dont la non dispo est bloquante empêche la réservation de se poursuivre (elle reste en Brouillon)"),
        "empruntable":fields.boolean("Se fournir à l'extérieur", help="indique si l'on peut emprunter cette ressource à des collectivités extèrieures"),
        "checkout_lines":fields.one2many('openstc.pret.checkout.line', 'product_id', string="Lignes Etat des Lieux"),
        'need_infos_supp':fields.boolean('Nécessite Infos Supp ?', help="Indiquer si, pour une Réservation, cette ressource nécessite des infos supplémentaires A saisir par le demandeur."),
        'service_technical_id':fields.many2one('openstc.service', 'Service Technique associé',help='Si renseigné, indique que cette ressource nécessite une manipulation technique pour être installée sur site, cette ressource est donc susceptible de générer une intervention sur ce service.'),
        'type_prod':fields.selection(_get_type_prod_values, 'Type de Produit'),
        }

    _defaults = {
        'seuil_confirm': 0,
        'need_infos_supp': lambda *a:0,
    }

product_product()


class hotel_reservation_line(osv.osv):
    _name = "hotel_reservation.line"
    _inherit = "hotel_reservation.line"

    _AVAILABLE_ACTION_VALUES = [('nothing','Pas d\'intervention'),('inter','Intervention à générer'),('inter_ok','Intervention générée')]

    def name_get(self, cr, uid, ids, context=None):
        ret = []
        for line in self.browse(cr, uid, ids, context):
            ret.append((line.id,'%s %s' % (line.qte_reserves, line.reserve_product)))
        return ret

    #Ligne valide si (infos XOR no_infos)
    def _calc_line_is_valid(self, cr, uid, ids, name, args, context=None):
        ret = {}
        for line in self.browse(cr, uid, ids):
            ret.update({line.id: (line.infos and not line.no_infos) or (not line.infos and line.no_infos)})
        return ret

    def _get_line_to_valide(self, cr, uid, ids, context=None):
        return ids

    def _get_state_line(self, cr, uid, context=None):
        res = self.pool.get("hotel.reservation").fields_get(cr, uid, 'state', context=context)
        return res['state']['selection']

    def _get_resa_id(self, cr, uid, ids, context=None):
        line_ids = []
        for resa in self.pool.get("hotel.reservation").browse(cr, uid, ids, context):
            #std case, in which user modify checkin or checkout
            if resa.state == 'remplir':
                return [x.id for x in resa.reservation_line]
            #if a resa is cancelled, terminated or confirmed, we re-check all resa with same products
            elif resa.state in ('cancle','done','confirm'):
                line_recompute_ids = self.pool.get("hotel_reservation.line").search(cr, uid, [('reserve_product','in',[x.reserve_product.id for x in resa.reservation_line]),('line_id.state','in',('remplir','draft','wait_confirm'))])
                return line_recompute_ids
        return line_ids
        """def _get_resa_line_id(self, cr, uid, ids, context=None):
        prod_ids = []
        for line in self.browse(cr, uid, ids, context):
            #if a record of a validated resa is unlinked, we have to adapt availability of all prod line at 'remplir'
            if not line.line_id and line.state in ('confirm','in_use'):
                prod_ids.append(line.reserve_product.id)
        if prod_ids:
            return self.search(cr, uid, [('reserve_product','in',(prod_ids)),('line_id.state','in',('remplir,draft,waiting_confirm'))])
        return ids"""
    
    def _get_resa_via_prods(self, cr, uid, ids, context=None):
        prod_ids = [x.product_id.id for x in self.pool.get("stock.inventory.line").browse(cr, uid, ids, context=context) if x.product_id]
        line_ids = self.pool.get("hotel_reservation.line").search(cr, uid, [('line_id.state','=','remplir'),('reserve_product','in',prod_ids)])
        return line_ids
    
    def _calc_qte_dispo(self, cr, uid, ids, name, args, context=None):
        prod_id_to_line = {}
        if not context:
            context = {}
        resa_ids = []
        ret = {}
        if 'qte_dispo' in name:
            #get all resa linked with lines
            for line in self.browse(cr, uid, ids):
                if line.line_id and not line.line_id.id in resa_ids:
                    resa_ids.append(line.line_id.id)
            #for each resa, compute the qty_available
            for resa in self.pool.get("hotel.reservation").browse(cr, uid, resa_ids):
                prod_ids = [x.reserve_product.id for x in resa.reservation_line]
                #get available prods_qty : {prod_id:qty}
                available = self.pool.get("hotel.reservation").get_prods_available_and_qty( cr, uid, resa.checkin, resa.checkout, prod_ids=prod_ids, where_optionnel='and hr.id <> ' + str(resa.id), context=context)
                #link prod qty available to resa_line associated
                for line in resa.reservation_line:
                    ret.update({line.id:{'qte_dispo':available[line.reserve_product.id]}})
                    if 'dispo' in name:
                        ret[line.id].update({'dispo':available[line.reserve_product.id] >= line.qte_reserves})
        elif 'dispo' in name:
            for line in self.browse(cr, uid, ids):
                ret.update({line.id:{'dispo':line.qte_dispo >= line.qte_reserves}})
        return ret

    def _calc_dispo(self, cr, uid, ids, name, args, context=None):
        ret = {}
        for line in self.browse(cr, uid, ids, context):
            ret[line.id] = line.qte_dispo >= line.qte_reserves
        return ret

    def _get_amount(self, cr, uid, ids, name, args, context=None):
        ret = {}.fromkeys(ids, 0.0)
        for line in self.browse(cr, uid, ids, context):
            amount = line.prix_unitaire * line.uom_qty
            ret[line.id] = amount
            #TOCHECK: is there any taxe when collectivity invoice people ?
        return ret

    _columns = {
        'categ_id': fields.many2one('product.category','Type d\'article'),
        "reserve_product": fields.many2one("product.product", "Article réservé", domain=[('type_prod','=','ressource')]),
        "qte_reserves":fields.float("Qté désirée", digits=(3,2)),
        "prix_unitaire": fields.float("Prix Unitaire", digit=(4,2)),
        #"dispo":fields.boolean("Disponible"),
        'dispo':fields.function(_calc_qte_dispo, string="Disponible", method=True, multi="dispo", type='boolean'),
#        store={'hotel.reservation':[_get_resa_id, ['state','checkin','checkout'], 10],
#        'hotel_reservation.line':[lambda self,cr,uid,ids,ctx:ids,['reserve_product','qte_dispo','qte_reserves'],11]}
        "infos":fields.char("Informations supplémentaires",size=256),
        #"no_infos":fields.boolean("Ne sais pas"),
        #"valide":fields.function(_calc_line_is_valid, method=True, type="boolean",
        #                         store={'hotel_reservation.line':(_get_line_to_valide, ['infos','no_infos'], 10),},
        #                         string="Ligne Valide"),
        "name":fields.char('Libellé', size=128),
        'state':fields.related('line_id','state', type='selection',string='Etat Résa', selection=_get_state_line, readonly=True),
        'uom_qty':fields.float('Qté de Référence pour Facturation',digit=(2,1)),
        'amount':fields.function(_get_amount, string="Prix (si onéreux)", type="float", method=True),
        'qte_dispo':fields.function(_calc_qte_dispo, method=True, string='Qté Dispo', multi="dispo", type='float'),
        'action':fields.selection(_AVAILABLE_ACTION_VALUES, 'Action'),
        'inter_ask_id':fields.many2one('openstc.ask','Demande d\'intervention associée'),

#        store={'hotel.reservation':[_get_resa_id, ['state','checkin','checkout'], 10],
#        'hotel_reservation.line':[lambda self,cr,uid,ids,ctx:ids, ['reserve_product'], 11],
#        'stock.inventory.line':[_get_resa_via_prods,['product_id','product_qty','inventory_id','location_id'],12]}

        }

    _defaults = {
     'qte_reserves':lambda *a: 1,
     'state':'remplir',
     'action':'nothing',
        }

    def write(self, cr, uid, ids, vals, context=None):
        res = super(hotel_reservation_line, self).write(cr, uid, ids, vals, context=context)
        if 'reserve_product' in vals or 'qte_reserves' in vals:
            resa_ids = self.read_group(cr, uid, [('id','in',ids),('line_id','<>',False)], ['line_id'], ['line_id'],context=context)
            self.pool.get("hotel.reservation").trigger_reserv_modified(cr, uid, [x['line_id'][0] for x in resa_ids], context)
        return res

    
    def plan_inter(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'action':'inter'})
        return {'type':'ir.actions.act_window.close'}

    def unplan_inter(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'action':'nothing'})
        return {'type':'ir.actions.act_window.close'}

    def open_inter(self, cr, uid, ids, context=None):
        if isinstance(ids, list):
            ids = ids[0]
        line = self.browse(cr, uid, ids, context)
        if not line.inter_ask_id:
            raise osv.except_osv("Erreur",u"L'intervention associée n'existe pas ou a été supprimée, impossible de la retrouver.")
        return {
            'type':'ir.actions.act_window',
            'target':'new',
            'res_model':'openstc.ask',
            'res_id':line.inter_ask_id.id,
            'view_mode':'form',
        }

hotel_reservation_line()

class hotel_reservation(osv.osv):
    AVAILABLE_IN_OPTION_LIST = [('no','Rien à Signaler'),('in_option','Réservation En Option'),('block','Réservation bloquée')]
    _name = "hotel.reservation"
    _inherit = "hotel.reservation"
    _description = "Réservations"

    def remove_accents(self, str):
        return ''.join(x for x in unicodedata.normalize('NFKD',str) if unicodedata.category(x)[0] == 'L')
    
    def _custom_sequence(self, cr, uid, context):
        seq = self.pool.get("ir.sequence").next_by_code(cr, uid, 'resa.number',context)
        user = self.pool.get("res.users").browse(cr, uid, uid)
        prog = re.compile('[Oo]pen[a-zA-Z]{3}/[Mm]anager')
        service = None
        if 'service_id' in context:
            service = context['service_id']
        for group in user.groups_id:
            if prog.search(group.name):
                if isinstance(user.service_ids, list) and not service:
                    service = user.service_ids[0]
                else:
                    service = self.pool.get("openstc.service").browse(cr, uid, service)
                seq = seq.replace('-xxx-','-' + self.remove_accents(service.name[:3]).upper() + '-')
                
        return seq

    def _calc_in_option(self, cr, uid, ids, name, args, context=None):
        print("début calc_in_option")
        ret = {}
        #fixes : calc only for resa, avoiding inheritance bugs
        for resa in self.pool.get("hotel.reservation").browse(cr, uid, ids, context):
            ret[resa.id] = 'no'
            date_crea = strptime(resa.date_order, '%Y-%m-%d %H:%M:%S')
            checkin = strptime(resa.checkin, '%Y-%m-%d %H:%M:%S')
            for line in resa.reservation_line:
                #Vérif si résa dans les délais, sinon, in_option est cochée
                d = timedelta(days=int(line.reserve_product.sale_delay))
                print("now :"+str(date_crea))
                print("checkin :" + str(checkin))
                #Si l'un des produits est hors délai
                if date_crea + d > checkin:
                    if line.reserve_product.bloquant:
                        ret[resa.id] = 'block'
                    elif ret[resa.id] == 'no':
                        ret[resa.id] = 'in_option'
        return ret

    def get_resa_modified(self, cr, uid, ids, context=None):
        return ids

    def return_state_values(self, cr, uid, context=None):
        return [('draft', 'Saisie des infos personnelles'),('confirm','Réservation confirmée'),('cancle','Annulée'),('in_use','Réservation planifiée'),('done','Réservation Terminée'), ('remplir','Saisie de la réservation'),('wait_confirm','En Attente de Confirmation')]

    def _get_state_values(self, cr, uid, context=None):
        return self.return_state_values(cr, uid, context)

    _columns = {
                'state': fields.selection(_get_state_values, 'Etat',readonly=True),
                'in_option':fields.function(_calc_in_option, string="En Option", selection=AVAILABLE_IN_OPTION_LIST, type="selection", method = True, store={'hotel.reservation':(get_resa_modified,['checkin','reservation_line'],10)},
                                            help=("Une réservation mise en option signifie que votre demande est prise en compte mais \
                                            dont on ne peut pas garantir la livraison à la date prévue.\
                                            Une réservation bloquée signifie que la réservation n'est pas prise en compte car nous ne pouvons pas \
                                            garantir la livraison aux dates indiquées")),
                'name':fields.char('Nom Manifestation', size=128, required=True),
                'partner_mail':fields.char('Email Demandeur', size=128, required=False),
                'is_recur':fields.boolean('Issue d\'une Récurrence', readonly=True),
                'site_id':fields.many2one('openstc.site','Site (Lieu)'),
                'prod_id':fields.many2one('product.product','Ressource'),
                'openstc_partner_id':fields.many2one('res.partner','Demandeur', help="Personne demandant la réservation."),
                'resa_checkout_id':fields.many2one('openstc.pret.checkout','Etat des Lieux associé'),
        }
    _defaults = {
                 'in_option': lambda *a :0,
                 'state': lambda *a: 'remplir',
                 'is_recur': lambda *a: 0,
                 'reservation_no': lambda self,cr,uid,ctx=None:self._custom_sequence(cr, uid, ctx),
        }
    _order = "checkin, in_option"
    
    def _check_dates(self, cr, uid, ids, context=None):
        for resa in self.browse(cr, uid, ids, context):
            if resa.checkin >= resa.checkout:
                return False
        return True
     
    _constraints = [(_check_dates, "La date de Début de votre réservation est supérieure A la date de Fin, veuillez les modifier.", ['checkin','checkout'])]


    def confirmed_reservation(self,cr,uid,ids):
        #self.write(cr, uid, ids, {'state':'confirm'})
        for resa in self.browse(cr, uid, ids):
            if self.is_all_dispo(cr, uid, ids[0]):
                #if self.is_all_valid(cr, uid, ids[0]):
                if resa.in_option == 'block':
                    raise osv.except_osv("Erreur","""Votre réservation est bloquée car la date de début de votre manifestion
                    ne nous permet pas de vous livrer dans les temps.""")

                attach_sale_id = []
                #TOCHECK: as long as form is written by employee, we let him all latitude to manage prices
                #Calcul montant de la résa
                form_amount = 0.0
                line_ids = []
                for line in resa.reservation_line:
                    form_amount += line.prix_unitaire * line.qte_reserves
                """amount = self.get_amount_resa(cr, uid, ids)
                #in the folowing case, user have not computed the prod prices
                if form_amount <> amount and resa.state == 'draft':
                    self.compute_lines_price(cr, uid, [resa.id])
                #ohterwise, we test on the form values and not the expected values
                elif resa.state == "wait_confirm":
                    amount = form_amount
                if amount > 0.0:
                """
                if form_amount > 0.0:
                #Si montant > 0 euros, générer sale order puis dérouler wkf jusqu'a édition facture
                    folio_id = self.create_folio(cr, uid, ids)
                    wf_service = netsvc.LocalService('workflow')
                    wf_service.trg_validate(uid, 'hotel.folio', folio_id, 'order_confirm', cr)
                    folio = self.pool.get("hotel.folio").browse(cr, uid, folio_id)
                    move_ids = []
                    for picking in folio.order_id.picking_ids:
                        for move in picking.move_lines:
                            #On crée les mvts stocks inverses pour éviter que les stocks soient impactés
                            self.pool.get("stock.move").copy(cr, uid, move.id, {'picking_id':move.picking_id.id,'location_id':move.location_dest_id.id,'location_dest_id':move.location_id.id,'state':'draft'})
                    #On mets a jour le browse record pour qu'il intégre les nouveaux stock moves
                    folio.refresh()
                    #On applique et on termine tous les stock moves (ceux créés de base par sale order et ceux créés ce dessus
                    for picking in folio.order_id.picking_ids:
                        move_ids.extend([x.id for x in picking.move_lines])
                    self.pool.get("stock.move").action_done(cr, uid, move_ids)
                    attach_sale_id.append(self.pool.get("sale.order")._create_report_attach(cr, uid, folio.order_id))
                #send mail with optional attaches on products and the sale order pdf attached
                self.envoyer_mail(cr, uid, ids, {'state':'validated'}, attach_ids=attach_sale_id)
                self.write(cr, uid, ids, {'state':'confirm'})
                return True
                #else:
                #    raise osv.except_osv("""Il manque des informations""","""Erreur, Vous devez soit fournir des précisions
                #    pour les articles réservés (lieu où les livrer et combien) soit cocher la case "ne sais pas".
                #    Si vous avez rempli les infos supplémentaires et coché la case "ne sais pas", veuillez la décocher. """)
                #    return False
            else:
                raise osv.except_osv("""Vous devez vérifier les disponibilités""","""Erreur de validation du formulaire: un ou plusieurs
                 de vos articles ne sont pas disponibles, ou leur disponibilité n'a pas encore été vérifiée.
                 Vous devez valider les disponibilités de vos articles via le bouton "vérifier disponibilités".""")
                return False
        return True

    def waiting_confirm(self, cr, uid, ids):
        form_amount = 0.0
        line_ids = []
        for resa in self.browse(cr, uid, ids):
            for line in resa.reservation_line:
                form_amount += line.prix_unitaire * line.qte_reserves
            amount = self.get_amount_resa(cr, uid, ids)
            if form_amount <> amount:
                self.compute_lines_price(cr, uid, [resa.id])
        self.envoyer_mail(cr, uid, ids, {'state':'waiting'})
        self.write(cr, uid, ids, {'state':'wait_confirm'})
        return True

    #Mettre à l'état cancle et retirer les mouvements de stocks (supprimer mouvement ou faire le mouvement inverse ?)
    def cancelled_reservation(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state':'cancle', 'reservation_line':self.uncheck_all_dispo(cr, uid, ids)})

        return True


    def drafted_reservation(self, cr, uid, ids):
        for resa in self.browse(cr, uid, ids):
            if self.is_all_dispo(cr, uid, ids[0]):
                #if self.is_all_valid(cr, uid, ids[0]):
                if resa.in_option == 'block':
                    raise osv.except_osv("Erreur","""Votre réservation est bloquée car la date de début de votre manifestion
                    ne nous permet pas de vous livrer dans les temps.""")
                if not resa.reservation_line:
                    raise osv.except_osv("Erreur","Vous n'avez saisie aucune ligne de réservation. Vous ne pouvez pas poursuivre sans saisir de lignes de réservations.")
                self.write(cr, uid, ids, {'state':'draft'})
                #TODO: Si partner_shipping_id présent, calculer prix unitaires
                if resa.openstc_partner_id:
                    self.compute_lines_price(cr, uid, [resa.id])
                return True
                #else:
                #    raise osv.except_osv("""Il manque des informations""","""Erreur, Vous devez soit fournir des précisions
                #    pour les articles réservés (lieu où les livrer et combien) soit cocher la case "ne sais pas".
                #    Si vous avez rempli les infos supplémentaires et coché la case "ne sais pas", veuillez la décocher. """)
                #    return False
            else:
                raise osv.except_osv("""Vous devez vérifier les disponibilités""","""Erreur de validation du formulaire: un ou plusieurs
                 de vos articles ne sont pas disponibles, ou leur disponibilité n'a pas encore été vérifiée.
                 Vous devez valider les disponibilités de vos articles via le bouton "vérifier disponibilités".""")
                return False
        return True

    def to_uncheck_reservation_lines(self, cr, uid, ids):
        self.write(cr, uid, ids, {'reservation_line':self.uncheck_all_dispo(cr, uid, ids)})
        return True

    def redrafted_reservation(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state':'remplir'})
        return True
    def in_used_reservation(self, cr, uid, ids):
        self.put_in_use_with_intervention(cr, uid, ids)
        self.write(cr, uid, ids, {'state':'in_use'})
        return True
    def done_reservation(self, cr, uid, ids):
        if isinstance(ids, list):
            ids = ids[0]
        resa = self.browse(cr, uid, ids)
        if resa.is_recur:
            #TODO: create invoice from scratch
            pass
        else:
            wf_service = netsvc.LocalService("workflow")
            inv_ids = []
            attach_ids = []
            #Create invoice from each folio
            for folio in resa.folio_id:
                wf_service.trg_validate(uid, 'hotel.folio', folio.id, 'manual_invoice', cr)
            resa.refresh()
            #Validate invoice(s) created
            for folio in resa.folio_id:
                for inv in folio.order_id.invoice_ids:
                    print(inv.state)
                    wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_open', cr)
                    inv_ids.append(inv.id)
            #send mail to notify user if opt_out not checked and if there is invoice(s)
            if inv_ids:
                #attaches = self.pool.get("ir.attachment").search(cr, uid, [('res_model_','=','account.invoice'),('res_id','in',inv_ids)])
                cr.execute("select id from ir_attachment where res_model = %s and res_id in %s", ('account.invoice',tuple(inv_ids)))
                attaches = [item[0] for item in cr.fetchall()]
                if not isinstance(attaches, list):
                    attaches = [attaches]
                self.envoyer_mail(cr, uid, [ids], vals={'state':'done'}, attach_ids=attaches)
        self.write(cr, uid, ids, {'state':'done'})
        return True
    def is_drafted(self, cr, uid, ids):
        for values in self.browse(cr, uid, ids):
            if values.state <> 'draft':
                return False
        return True

    def is_not_drafted(self, cr, uid, ids):
        return not self.is_drafter

    def need_confirm(self, cr, uid, ids):
        reservations = self.browse(cr, uid, ids)
        etape_validation = False
        prog = re.compile(u'[Oo]pen(STC|[SC]TM)/[Mm]anager')
        groups = self.pool.get("res.users").browse(cr, uid, uid, context=None).groups_id
        #if group == "Responsable", no need confirm
        for group in groups:
            if prog.search(group.name):
                return False
        #else, check each seuil confirm products
        for resa in reservations:
                for line in resa.reservation_line:
                    #Si l'un des produits dépasse le seuil max autorisé, on force la validation
                    if line.qte_reserves > line.reserve_product.seuil_confirm:
                        etape_validation = True
        return etape_validation
        #return True

    def not_need_confirm(self, cr, uid, ids):
        return not self.need_confirm(cr, uid, ids)

    def ARemplir_reservation(self, cr, uid, ids):
        #TOCHECK: Voir quand il faut mettre la résa à l'état "in_option" : Clique sur Suivant malgré non dispo ?
        print("Mise à l'état remplir")
        self.write(cr, uid, ids, {'state':'remplir'})
        return True

    #Cette fonction déclenche le signal "reserv_modified" du wkf pour indiquer qu'il faut refaire
    #l'étape de validation de dispo (on revient à l'état "A Remplir" Pour valider les modifs.
    def trigger_reserv_modified(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        for id in ids:
            wf_service.trg_validate(uid, 'hotel.reservation', id, 'reserv_modified', cr)
        return True

    #Fonction (liée à une action) permettant de pré-remplir la fiche de réservation en fonction des infos du ou des articles sélectionnés
    def default_get(self, cr, uid, fields, context=None):
        res = super(hotel_reservation, self).default_get(cr, uid, fields, context=context)
        #Si pour l'initialisation de la vue, on est passé par l'action "Réserver article(s)" associée aux catalogues produits
        if ('from_product' in context) and (context['from_product']=='1') :
            data = context and context.get('product_ids', []) or []
            produit_obj = self.pool.get('product.product')
            #produit_obj = self.pool.get('hotel.room')
            #Pour chaque produit sélectionnés dans la vue tree des catalogues, on crée une ligne de réservation (objet hotel.reservation.line)
            reservation_lines = []
            for produit in produit_obj.browse(cr, uid, data, []):
                reservation_lines.append(self.pool.get('hotel_reservation.line').create(cr, uid, {
                                                                                        'reserve_product':  produit.id,
                                                                                        'categ_id':produit.categ_id.id,
                                                                                        'reserve':[(4, produit.id)],
                                                                                        'prix_unitaire':produit.product_tmpl_id.list_price,
                                                                                        'qte_reserves':10
                                                                                }))

            res.update({'reservation_line':reservation_lines})
        #Valeurs par défauts des champs cachés
        return res

    def get_nb_prod_reserved(self, cr, prod_list, checkin, checkout, states=['cancle','done','remplir'], where_optionnel=""):
        print("début get_nb_prod_reserved")
        cr.execute("select reserve_product, sum(qte_reserves) as qte_reservee \
                    from hotel_reservation as hr, \
                    hotel_reservation_line as hrl \
                    where hr.id = hrl.line_id \
                    and reserve_product in %s \
                    and hr.state not in%s \
                    and (hr.checkin, hr.checkout) overlaps ( timestamp %s, timestamp %s ) \
                    " + where_optionnel + " \
                    group by reserve_product; ", (tuple(prod_list), tuple(states), checkin, checkout))
        """line_ids = self.pool.get("hotel_reservation.line").search(cr, uid, [('reserve_product','in',prod_list), 'line_id.state','in',('confirm','in_use'),
                                                                 '|','|','&',('checkin','<=',checkout),('checkout','>=',checkout),
                                                                 '&',('checkin','<=',checkin),('checkout','>=',checkin),
                                                                 '&',('checkin','>',checkin),('checkout','<',checkout)])
        """
        return cr
    
    #@deprecated: use get_prods_available_and_qty instead of this one
    def check_dispo(self, cr, uid, id=0, default_checkin=False, default_checkout=False, prod_dict=None, context=None):
        reservation = self.browse(cr, uid, id)
        if not prod_dict:
            prod_dict = {}
        if isinstance(reservation, list):
            reservation = reservation[0]
        checkin = default_checkin or reservation.checkin
        checkout = default_checkout or reservation.checkout
        reserv_vals = {} if prod_dict else reservation.reservation_line
        demande_prod = prod_dict
        prod_list = prod_dict.keys() or []
        prod_list_all = prod_dict.keys() or []
        my_where_optionnel = ""
        if id:
            my_where_optionnel = "and hr.id <> " + str(id)
        if not (demande_prod or reserv_vals):
            raise osv.except_osv("Erreur","Vous n'avez saisie aucune ligne de réservation. Vous ne pouvez pas poursuivre sans saisir de lignes de réservations.")
        
        #Parcours des lignes de réservation pour 
        for line in reserv_vals:
            #Récup des produits à réserver
            prod_list.append(line.reserve_product.id)
            prod_list_all.append(line.reserve_product.id)
            demande_prod[line.reserve_product.id] = line.qte_reserves
        
        #Vérif dispo pour chaque produit
        ok = True
        #On vérifie que l'on a récupéré au moins un produit
        #Dictionnaire des qtés totales de chaque produit de la demande en cours
        stock_prod = self.pool.get("product.product")._product_available(cr, uid, prod_list, ['virtual_available'])
        #Liste des produits non disponibles
        print(stock_prod)
        dict_error_prod = {}
        #NOTES:chaque produit que l'on récupère de la requête sql indique que ce produit a été loué au moins une fois
        #Ainsi, si un produit figure dans la demande en cours mais non présent dans le résultat sql, c'est qu'on n'a jamais réservé ce produit
        results = self.get_nb_prod_reserved(cr, prod_list, checkin, checkout, where_optionnel=my_where_optionnel).fetchall()
        ok = results and ok or False
        print(ok)
        #Vérif dispo : Cas d'un produit déjà loué
        for data in results:
            qte_total_prod = stock_prod[data[0]]['virtual_available']
            qte_voulue = demande_prod[data[0]]
            #Si l'un des produits n'est pas dispo, on annule la réservation des articles
            #TOCHECK:la réservation reste à l'état draft
            #on vérifie si le produit est dispo en quantité suffisante : stock total - qtés déjà résevées - qtés voulues
            if qte_total_prod < data[1] + qte_voulue:
                ok = False
                dict_error_prod[data[0]] = [qte_voulue, qte_total_prod - data[1]]
            prod_list.remove(data[0])
        #Vérif dispo : Cas où on réserve un produit pour la première fois, autrement dit, s'il reste des occurences dans prod_list
        for prod_id in prod_list:
             ok = True
             qte_total_prod = stock_prod[prod_id]['virtual_available']
             qte_voulue = demande_prod[prod_id]
             if qte_total_prod < qte_voulue:
                 ok = False
                 dict_error_prod[prod_id] = [qte_voulue, qte_total_prod]
        print(ok)
        """#Si on a cliqué sur "vérifier dispo", on fait seulement un update des lignes de résa sur le champs dispo
        if 'update_line_dispo' in context:
            line_prod_ids_dispo = self.pool.get("hotel_reservation.line").search(cr, uid, [('line_id', '=',id),('reserve_product','in',prod_list_all)])
            #print (line_prod_ids_dispo)
            line_prod_ids_non_dispo = self.pool.get("hotel_reservation.line").search(cr, uid, [('line_id', '=',id),('reserve_product','in',dict_error_prod.keys())])
            #print(line_prod_ids_non_dispo)

            list_for_update = []
            #Par défaut tous les produits sont dispo
            for line_id in line_prod_ids_dispo:
                list_for_update.append((1, line_id,{'dispo':True},))
            #print(list_for_update)
            if list_for_update:
                self.write(cr, uid, [id], {'reservation_line':list_for_update})

            list_for_update = []
            #Et on mets à jour les lignes dont le produit n'est pas dispo
            for line_id in line_prod_ids_non_dispo:
                list_for_update.append((1, line_id,{'dispo':False}),)
            #print(list_for_update)
            if list_for_update:
                self.write(cr, uid, [id], {'reservation_line':list_for_update})"""

        """if not ok:
            prod_error_str = ""
            for prod_error in self.pool.get("product.product").browse(cr, uid, dict_error_prod.keys()):
                if prod_error_str <> "":
                    prod_error_str +=", "
                prod_error_str += str(dict_error_prod[prod_error.id][0]) + " x " + prod_error.name + "( " + str(dict_error_prod[prod_error.id][1]) + " disponibles pour ces dates)"
            if not 'update_line_dispo' in context:
                raise osv.except_osv("Produit(s) non disponible(s)","Votre réservation n'a pas aboutie car \
                les produits suivants ne sont pas disponibles pour la période " + checkin + " - " + checkout + ":\
                " + prod_error_str)"""
        return dict_error_prod, prod_list_all

    #Bouton pour vérif résa, mets à jour les champs dispo de chaque ligne de résa
    def verif_dispo(self,cr ,uid, ids, context=None):
        context['update_line_dispo'] = 1
        list_prod_error = {}
        ok = True
        for id in ids:
            list_prod_error, prod_list_all = self.check_dispo(cr, uid, id, context=context)
            if list_prod_error:
                ok = False
        #S'il y a une erreur de dispo, on affiche un wizard donnant accès à l'action d'emprunt des articles ou de visualisation du planning
        if not ok:
           ret = {'view_mode':'form',
                   'res_model':'openstc.pret.warning.dispo.wizard',
                   'type':'ir.actions.act_window',
                   'context':{'prod_error_ids':list_prod_error,
                              'reservation_id':id,
                              'all_prods':prod_list_all},
                  'target':'new',
                  }

           return ret
        #S'il n'y a pas d'erreurs dans la réservation, on poursuit le processus normal
        return {'view_mode': 'form,tree',
                'res_model': 'hotel.reservation',
                'type': 'ir.actions.act_window',
                'res_id':ids[0]
                }

    def get_prods_available(self, cr, uid, checkin, checkout, prod_ids=[], context=None):
        #TODO: add alternative return, which indicates qty of prod_available (useful for multi-qty reservation)
        if not context:
            context = {}
        prod_dict = {}
        if isinstance(prod_ids, list):
            for id in prod_ids:
                prod_dict.update({id:1})
        elif isinstance(prod_ids, dict):
            prod_dict = prod_ids
        else:
            #Print for log errors
            print("prod_ids error : " + prod_ids)
            raise osv.except_osv("Erreur","Une erreur est apparue, veuillez notifier l'erreur suivante A votre prestataire : \n la paramètre prod_ids de la méthode get_prods_available est d'une forme incorrecte.")
        #Get availability of prods : (dict_error, all_prods)
        res = self.check_dispo(cr, uid, 0, checkin, checkout, prod_dict, context)
        #Format result to return only prods available
        ret = [id for id in res[1] if id not in res[0].keys()]
        return ret
    
    #main method to control availability of products : returns availability of each prod : {prod_id:qty} matching dates
    def get_prods_available_and_qty(self, cr, uid, checkin, checkout, prod_ids=[], where_optionnel='', context=None):
        #if no prod_ids put, we check all prods
        if not prod_ids:
            prod_ids = self.pool.get("product.product").search(cr, uid, [])
        prods = self.pool.get("product.product").browse(cr, uid, prod_ids)
        prod_dispo = {}
        #by default, all qty in stock are available
        for prod in prods:
            prod_dispo.setdefault(prod.id, prod.virtual_available)
        #and, if some resa are made to this prods, we substract default qty with all qty reserved at these dates
        results = self.get_nb_prod_reserved(cr, prod_ids, checkin, checkout, where_optionnel=where_optionnel).fetchall()
        for prod_id, qty_reserved in results:
            prod_dispo[prod_id] -= qty_reserved
        return prod_dispo
    
        """def get_prods_available_and_qty(self, cr, uid, checkin, checkout, prod_ids=[], context=None):
        if not context:
            context = {}
        prod_dict = {}
        if isinstance(prod_ids, list):
            for prod in self.pool.get("product.product").browse(cr, uid, prod_ids, context):
                prod_dict.update({prod.id:prod.virtual_available + 1.0})
        elif isinstance(prod_ids, dict):
            prod_dict = prod_ids
        else:
            #Print for log errors
            print("prod_ids error : " + prod_ids)
            raise osv.except_osv("Erreur","Une erreur est apparue, veuillez notifier l'erreur suivante A votre prestataire : \n la paramètre prod_ids de la méthode get_prods_available est d'une forme incorrecte.")
        #Get availability of prods : (dict_error, all_prods)
        res = self.check_dispo(cr, uid, 0, checkin, checkout, prod_dict, context)
        if res[0]:
            ret = {}
            for key, value in res[0].items():
                ret.update({key:value[1]})
            return ret
        return False"""
    
    #Vérifies les champs dispo de chaque ligne de résa pour dire si oui ou non la résa est OK pour la suite
    #TODO: Voir comment gérer le cas de la reprise d'une résa à revalider / incomplète où des champs dispo sont à True
    #=> Problème lorsque quelqu'un d'autre réserve un même produit
    def is_all_dispo(self, cr, uid, id, context=None):
        for line in self.browse(cr, uid, id, context).reservation_line:
            if not line.dispo:
                return False
        return True

    def is_all_valid(self, cr, uid, id, context=None):
        for line in self.browse(cr, uid, id, context).reservation_line:
            if not line.valide and line.reserve_product.need_infos_supp:
                return False
        return True

    #Renvoies actions bdd permettant de mettre toutes les dispo de la résa à False
    #Ne renvoie que les actions de mises à jours des lignes déjà enregistrées dans la réservation
    def uncheck_all_dispo(self, cr, uid, ids, context=None):
        line_ids = self.pool.get("hotel_reservation.line").search(cr, uid, [('line_id','in',ids)])
        reservation_line = []
        for line in line_ids:
            reservation_line.append((1,line,{'dispo':False, 'valide':False}))
        return reservation_line

    #polymorphism of _create_folio
    def create_folio(self, cr, uid, ids, context=None):
        for reservation in self.browse(cr,uid,ids):
            room_lines = []
            for line in reservation.reservation_line:
                room_lines.append((0,0,{
                   'checkin_date':reservation['checkin'],
                   'checkout_date':reservation['checkout'],
                   'product_id':line.reserve_product.id,
                   'name':line.reserve_product.name_template,
                   'product_uom':line.reserve_product.uom_id.id,
                   'price_unit':line.prix_unitaire,
                   'product_uom_qty':line.uom_qty

                   }))
            folio=self.pool.get('hotel.folio').create(cr,uid,{
                  'date_order':reservation.date_order,
                  'shop_id':reservation.shop_id.id,
                  'partner_id':reservation.partner_id.id,
                  'pricelist_id':reservation.pricelist_id.id,
                  'partner_invoice_id':reservation.partner_invoice_id.id,
                  'partner_order_id':reservation.partner_order_id.id,
                  'partner_shipping_id':reservation.partner_shipping_id.id,
                  'checkin_date': reservation.checkin,
                  'checkout_date': reservation.checkout,
                  'room_lines':room_lines,
           })
            cr.execute('insert into hotel_folio_reservation_rel (order_id,invoice_id) values (%s,%s)', (reservation.id, folio))

        return folio
        """return {
                'view_mode': 'form,tree',
                'res_model': 'hotel.folio',
                'type': 'ir.actions.act_window',
                'res_id':folio,
                'target':'new'
                }"""

    #param record: browse_record hotel.reservation.line
    def get_prod_price(self, cr, uid, ids, record, context=None):
        pricelist_obj = self.pool.get("product.pricelist")
        pricelist_id = record.line_id.partner_id.property_product_pricelist.id
        res = pricelist_obj.price_get_multi(cr, uid, [pricelist_id], [(record.reserve_product.id,record.qte_reserves,record.line_id.partner_id.id)], context=None)
        return res and res[record.reserve_product.id][pricelist_id] or False
        #return record.reserve_product.product_tmpl_id.standard_price

    #param record: browse_record hotel.reservation.line
    #if product uom refers to a resa time, we compute uom according to checkin, checkout
    def get_prod_uom_qty(self, cr, uid, ids, record, length, context=None):
        if re.search(u"[Rr]{1}[ée]{1}servation", record.reserve_product.uom_id.category_id.name):
            #uom factor refers to journey, to have uom factor refering to hours, we have to adust ratio
            factor = 24.0 / record.reserve_product.uom_id.factor
            res = length / factor
            #round to direct superior int
            #TODO: here we can apply an adjustment to decide the max decimal value before passing to superior int
            if res > int(res):
                res = int(res) + 1.0
        else:
            res = record.qte_reserves
        return res

    def get_length_resa(self, cr, uid, id, context=None):
        resa = self.browse(cr, uid, id, context)
        checkin = strptime(resa.checkin, '%Y-%m-%d %H:%M:%S')
        checkout = strptime(resa.checkout, '%Y-%m-%d %H:%M:%S')
        length = (checkout - checkin).hours
        return length

    def get_amount_resa(self, cr, uid, ids, context=None):
        pricelist_obj = self.pool.get("product.pricelist")
        for resa in self.browse(cr, uid, ids ,context):
            pricelist = resa.partner_id.property_product_pricelist.id
            amount = 0.0
            values = []
            for line in resa.reservation_line:
                #TOREMOVE: for each prod, gets price from table price
                #amount += self.get_prod_price(cr, uid, ids, line, context) * line.qte_reserves
                #TODO: for each prod, gets price from pricelist
                values.append((line.reserve_product.id,line.qte_reserves, resa.partner_id.id))
            pricelist_obj = self.pool.get("product.pricelist")
            res = pricelist_obj.price_get_multi(cr, uid, [pricelist], values, context=None)
            #compute amount with price_unit got
            for line in resa.reservation_line:
                amount += res[line.reserve_product.id][pricelist]
        return amount

    def compute_lines_price(self, cr, uid, ids, context=None):
        values = []
        #get lentgh resa in hours
        for resa in self.browse(cr, uid, ids, context):
            length_resa = self.get_length_resa(cr, uid, resa.id, context=None)
            values.extend([(1,line.id,{'prix_unitaire':self.get_prod_price(cr, uid, resa.id, line, context),
                                       'uom_qty':self.get_prod_uom_qty(cr, uid, resa.id, line, length_resa, context)}) for line in resa.reservation_line])
            self.write(cr, uid, [resa.id], {'reservation_line':values}, context=context)
        return True

    def open_checkout(self, cr, uid, ids, context=None):
        if isinstance(ids, list):
            ids = ids[0]
        ret = {
            'type':'ir.actions.act_window',
            'res_model':'openstc.pret.checkout',
            'view_type':'form',
            'view_mode':'form',
            'target':'new',
            }
        if not context:
            context = {}
        context.update({'reservation_id':ids})
        #if a checkout already exists, we open to the existing id
        resa = self.browse(cr, uid, ids, context)
        if resa.resa_checkout_id:
            ret.update({'res_id':resa.resa_checkout_id.id})
        else:
            #else, we create a new checkout and display it in a new window(we force the creation to be sure that the checkout is saved in db)
            #we get default_values defined in default_get
            values = self.pool.get("openstc.pret.checkout").default_get(cr, uid, [], context=context)
            res_id = self.pool.get("openstc.pret.checkout").create(cr, uid, values)
            ret.update({'res_id':res_id})
        #and display it
        return ret

    def put_in_use_with_intervention(self, cr, uid, ids, context=None):
        if not context:
            context={}
        for resa in self.browse(cr, uid, ids, context):
            #Générer intervention de livraison et interventions optionnelles
            checkin = datetime.strptime(resa.checkin, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
            checkout = datetime.strptime(resa.checkout, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
            checkin_str = checkin.astimezone(pytz.timezone('Europe/Paris')).strftime('%x à %H:%M')
            checkout_str = checkout.astimezone(pytz.timezone('Europe/Paris')).strftime('%x à %H:%M')
            user = self.pool.get("res.users").browse(cr, uid, uid, context=context)
            partner = user.company_id.partner_id        
            inter_ask = []
            lines_grouped = {}
            for line in resa.reservation_line:
                if line.action == 'inter':
                    #group resa line by service_id
                    if not line.reserve_product.service_technical_id:
                        raise osv.except_osv("Erreur",_("Vous devez spécifier un service pour cet article : %s") %(line.reserve_product.name_template))
                    lines_grouped.setdefault(line.reserve_product.service_technical_id.id, [])
                    lines_grouped[line.reserve_product.service_technical_id.id].append(line)
            for service_id, lines in lines_grouped.items():
                #generate inter for each service, and compute strings according to lines matches this service_id
                name = ''
                name += ','.join(['%s %s ' % (str(line.qte_reserves) ,line.reserve_product.name_template) for line in lines])
                site_details = '\n'.join(['%s: %s ' % (line.reserve_product.name_template, line.infos) for line in lines if line.infos])
                values = {'name':_('[Evénementiel] Mise en place de %s sur le site %s') % (name, resa.site_id and resa.site_id.name or 'inconnu'), 
                          'site_details':site_details,
                          'description':_('Mise en place de %s sur le site %s dans le cadre de l\'événement "%s" prévue du %s au %s') %(name,resa.site_id and resa.site_id.name or 'inconnu', resa.name, checkin_str, checkout_str),
                          'partner_id':partner.id, 
                          'partner_address':partner.address[0].id,
                          'partner_type':partner.type_id and partner.type_id.id or False,
                          'partner_type_code':partner.type_id and partner.type_id.code or False,
                          'site1':resa.site_id.id,
                          'service_id':service_id,
                          'state':'wait',
                          }
                ret = self.pool.get("openstc.ask").create(cr, uid, values, context=context)
                if ret:
                    line_ids = [x.id for x in lines]
                    self.pool.get("hotel_reservation.line").write(cr, uid, line_ids, {'action':'inter_ok','inter_ask_id':ret})
                else:
                    print("Error when creating intervention with values : ")
                    print(values)
            line_with_no_ids = []    
        return {'type':'ir.actions.act_window_close'}

    #Vals: Dict containing "to" (deprecated) and "state" in ("error","draft", "confirm") (required)
    def envoyer_mail(self, cr, uid, ids, vals=None, attach_ids=[], context=None):
        #TOREMOVE: model.template A déplacer vers un fichier init.xml
        #TOREMOVE: Si le modèle n'existe pas, on le crée à la volée
        #TODO: check if company wants to send email (info not(opt_out) in partner)
        #We keep only resa where partner have not opt_out checked
        resa_ids_notif = []
        resa_ids_notif = [resa.id for resa in self.browse(cr, uid, ids) if not resa.partner_id.opt_out]
        if resa_ids_notif:
            email_obj = self.pool.get("email.template")
            email_tmpl_id = 0
            prod_attaches = {}
            if 'state' in vals.keys():
                if vals['state'] == "error":
                    email_tmpl_id = email_obj.search(cr, uid, [('model','=',self._name),('name','ilike','annulée')])
                    if not email_tmpl_id:
                        ir_model = self.pool.get("ir.model").search(cr, uid, [('model','=',self._name)])
                        email_tmpl_id = email_obj.create(cr, uid, {
                                                    'name':_('modèle de mail pour résa annulée'),
                                                    'name':'Réservation Annulée',
                                                    'model_id':ir_model[0],
                                                    'subject':_('Votre Réservation du ${object.checkin} au ${object.checkout} a été annulée'),
                                                    'email_from':_('bruno.plancher@gmail.com'),
                                                    'email_to':_('bruno.plancher@gmail.com'),
                                                    'body_text':_("Votre Réservation normalement prévue du ${object.checkin} au \
        ${object.checkout} dans le cadre de votre manifestation : ${object.name} a été annulée,\
        pour plus d'informations, veuillez contacter la mairie de Pont L'abbé au : 0240xxxxxx"),
                                                    'body_html':_("Votre Réservation normalement prévue du ${object.checkin} au \
        ${object.checkout} dans le cadre de votre manifestation : ${object.name} a été annulée,\
        pour plus d'informations, veuillez contacter la mairie de Pont L'abbé au : 0240xxxxxx")
                                                   })
                elif vals['state'] == 'validated':
                    email_tmpl_id = email_obj.search(cr, uid, [('model','=',self._name),('name','ilike','Réserv%Valid%')])
                    #Search for product attaches to be added to email
                    prod_ids = []
                    for resa in self.browse(cr, uid, ids):
                        prod_ids.extend([line.reserve_product.id for line in resa.reservation_line])
                    cr.execute("select id, res_id from ir_attachment where res_id in %s and res_model=%s order by res_id", (tuple(prod_ids), 'product.product'))
                    #format sql return to concat attaches with each prod_id
                    
                    for item in cr.fetchall():
                        prod_attaches.setdefault(item[1],[])
                        prod_attaches[item[1]].append(item[0])
                elif vals['state'] == 'waiting':
                    email_tmpl_id = email_obj.search(cr, uid, [('model','=',self._name),('name','ilike','Réserv%Attente')])
                elif vals['state'] == 'done':
                    email_tmpl_id = email_obj.search(cr, uid, [('model','=',self._name),('name','ilike','Réserv%Termin')])
                if email_tmpl_id:
                    if isinstance(email_tmpl_id, list):
                        email_tmpl_id = email_tmpl_id[0]
                    #Envoi du mail proprement dit, email_tmpl_id définit quel mail sera envoyé
                    for resa in self.browse(cr, uid, resa_ids_notif):
                        #link attaches of each product
                        attach_values = []
                        for line in resa.reservation_line:
                            if prod_attaches.has_key(line.reserve_product.id):
                                attach_values.extend([(4,attach_id) for attach_id in prod_attaches[line.reserve_product.id]])
                        #and link optional paramter attach_ids
                        attach_values.extend([(4,x) for x in attach_ids])
                        mail_id = email_obj.send_mail(cr, uid, email_tmpl_id, resa.id)
                        self.pool.get("mail.message").write(cr, uid, [mail_id], {'attachment_ids':attach_values})
                        self.pool.get("mail.message").send(cr, uid, [mail_id])
    
        return

    #Surcharge methode pour renvoyer uniquement les resas a traiter jusqu'au vendredi prochain, si on veut la vue associee aux resas a traiter par le responsable
    def search(self, cr, uid,args, offset=0, limit=None, order=None, context=None, count=False):
        #datetime.datetime.now() + datetime.timedelta(days=int(datetime.datetime.now().weekday()) / 4) * (7 - int(datetime.datetime.now().weekday())) + (4 - int(datetime.datetime.now().weekday()) * (1 - int(datetime.datetime.now().weekday()) / 4))
        if context and 'resa_semaine' in context:
            now = datetime.now()
            delta_day = 0
            if now.weekday() >= 4:
                #Si on dépasse jeudi, on fait les calculs pour retomber sur lundi prochain
                #7 - now.weekday() pour tomber sur lundi, +4 pour tomber sur vendredi à chaque fois
                delta_day = 7 + 4 - now.weekday()
            else:
                #Sinon, c'est qu'on est inférieur à jeudi, on reste dans la meme semaine
                delta_day = 4 - now.weekday()
            end_date = now + timedelta(days=delta_day)
            args.extend(['|',('checkout','<=',str(end_date)),('checkin','<=',str(end_date))])
            del context['resa_semaine']
        ret = super(hotel_reservation,self).search(cr, uid,args, offset, limit, order, context, count)
        return ret

    def create(self, cr, uid, vals, context=None):
        #Si on vient de créer une nouvelle réservation et qu'on veut la sauvegarder (cas où l'on appuie sur
        #"vérifier disponibilités" juste après la création (openERP force la sauvegarde)
        #Dans ce cas, on mets des valeurs par défauts pour les champs obligatoires
        print(vals)
        if not 'state' in vals or vals['state'] == 'remplir':
            vals['shop_id'] = self.pool.get("sale.shop").search(cr, uid, [], limit=1)[0]
            """vals['partner_id'] = self.pool.get("res.partner").search(cr, uid, [], limit=1)[0]
            part_vals = self.onchange_partner_id( cr, uid, [], vals['partner_id'])
            for (cle, data) in part_vals['value'].items():
                vals[cle] = data"""
        if 'checkin' in vals:
            vals['checkin'] = vals['checkin'][:-5] + '00:00'
        if 'checkout' in vals:
            vals['checkout'] = vals['checkout'][:-5] + '00:00'
        return super(hotel_reservation, self).create(cr, uid, vals, context)
        #TOCHECK: Vérif utilité, supprimer puis tester si tout fonctionne

    def write(self, cr, uid, ids, vals, context=None):
        #if dates are modified, we uncheck all dispo to force user to re check all lines
        if context == None:
            context = {}
        if 'checkin' in vals:
            vals['checkin'] = vals['checkin'][:-5] + '00:00'
        if 'checkout' in vals:
            vals['checkout'] = vals['checkout'][:-5] + '00:00'
        res = super(hotel_reservation, self).write(cr, uid, ids, vals, context)
        #if 'checkin' in vals or 'checkout' in vals:
        #    self.trigger_reserv_modified(cr, uid, ids, context)
        return res

    def unlink(self, cr, uid, ids, context):
        if not isinstance(ids, list):
            ids = [ids]
        line_ids = []
        for resa in self.browse(cr, uid, ids, context):
            line_ids.extend([x.id for x in resa.reservation_line])
        self.pool.get("hotel_reservation.line").unlink(cr, uid, line_ids, context)
        return super(hotel_reservation, self).unlink(cr, uid, ids, context)

    def onchange_in_option(self, cr, uid, ids, in_option=False, state=False, context=None):
        #TOREMOVE:
        #if in_option:
            #Affichage d'un wizard pour simuler une msgbox
        if in_option:
            return {'warning':{'title':'Réservation mise en option', 'message': '''Attention, Votre réservation est "hors délai"
            , nous ne pouvons pas vous assurer que nous pourrons vous livrer.'''}}

        return {'value':{}}

    def onchange_openstc_partner_id(self, cr, uid, ids, openstc_partner_id=False):
        return {'value':{'partner_id':openstc_partner_id}}

    """def onchange_partner_id(self, cr, uid, ids, part):
        vals = super(hotel_reservation, self).onchange_partner_id(cr, uid, ids, part)
        if part:
            vals['value']['partner_mail'] = self.pool.get("res.partner.address").browse(cr, uid, vals['value']['partner_invoice_id']).email
        return vals"""

    #Recalcul des coûts de produit
    """def onchange_partner_shipping_id(self, cr, uid, ids, partner_shipping_id=False, context=None):
        #TOCHECK: check if it's usefull
        #TODO: if it is, replace with compute_lines_price method
            ret = []
            if isinstance(ids, list):
                ids = ids[0]
            if partner_shipping_id:
                resa = self.browse(cr, uid, ids, context)
                for line in resa.reservation_line:
                    ret.append((1,line.id,{'prix_unitaire':self.get_prod_price(cr, uid, ids, line, context)}))
            return {'value':{'reservation_line':ret}}"""
        
    def onchange_partner_shipping_id(self, cr, uid, ids, partner_shipping_id=False):
        if partner_shipping_id:
            email = self.pool.get("res.partner.address").browse(cr, uid, partner_shipping_id).email
        return {'value':{'partner_mail':email}}
hotel_reservation()


class product_category(osv.osv):
    _name = "product.category"
    _inherit = 'product.category'
    _description = "Product Category"
    _columns = {
        'cat_id':fields.many2one('product.category','category', ondelete='cascade'),

    }
    _defaults = {
        'isroomtype': lambda *a: 1,
    }
product_category()

class purchase_order(osv.osv):
    _inherit = "purchase.order"
    _name = "purchase.order"
    _columns = {'is_emprunt':fields.boolean('Demande d\'emprunt', help="Indique qu'il s'agit d'une demande d'emprunt aurpès d'une mairie extèrieure et non d'un bon de commande")}
    _defaults = {
                 'is_emprunt':lambda *a: 0,
                 }

    def emprunt_done(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state':'done'})
        return True

    #Force purchase.order workflow to cancel its pickings (subflow returns cancel and reactivate workitem at picking activity)
    def do_terminate_emprunt(self, cr, uid, ids, context=None):
        list_picking_ids = []
        wf_service = netsvc.LocalService('workflow')
        for purchase in self.browse(cr, uid, ids):
            for picking in purchase.picking_ids:
                wf_service.trg_validate(uid, 'stock.picking', picking.id, 'button_cancel', cr)
            wf_service.trg_write(uid, 'purchase.order', purchase.id, cr)
            
        return {
                'res_model':'purchase.order',
                'type:':'ir.actions.act_window',
                'view_mode':'form',
                'target':'current',
                }
purchase_order()

class sale_order(osv.osv):
    _inherit = "sale.order"
    _name = "sale.order"

    #TODO: create custom jasper report instead of classic pdf report
    def _create_report_attach(self, cr, uid, record, context=None):
        #sources insipered by _edi_generate_report_attachment of EDIMIXIN module
        ir_actions_report = self.pool.get('ir.actions.report.xml')
        matching_reports = ir_actions_report.search(cr, uid, [('model','=',self._name),
                                                              ('report_type','=','pdf')])
        ret = False
        if matching_reports:
            report = ir_actions_report.browse(cr, uid, matching_reports[0])
            report_service = 'report.' + report.report_name
            service = netsvc.LocalService(report_service)
            (result, format) = service.create(cr, uid, [record.id], {'model': self._name}, context=context)
            eval_context = {'time': time, 'object': record}
            if not report.attachment or not eval(report.attachment, eval_context):
                # no auto-saving of report as attachment, need to do it manually
                result = base64.b64encode(result)
                file_name = record.name_get()[0][1]
                file_name = re.sub(r'[^a-zA-Z0-9_-]', '_', file_name)
                file_name += ".pdf"
                ir_attachment = self.pool.get('ir.attachment').create(cr, uid,
                                                                      {'name': file_name,
                                                                       'datas': result,
                                                                       'datas_fname': file_name,
                                                                       'res_model': self._name,
                                                                       'res_id': record.id},
                                                                      context=context)
                ret = ir_attachment
        return ret

sale_order()

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    _name = "account.invoice"
    
    _columns = {
        }
    
        #TODO: create custom jasper report instead of classic pdf report
    def _create_report_attach(self, cr, uid, record, context=None):
        #sources insipered by _edi_generate_report_attachment of EDIMIXIN module
        ir_actions_report = self.pool.get('ir.actions.report.xml')
        matching_reports = ir_actions_report.search(cr, uid, [('model','=',self._name),
                                                              ('report_type','=','pdf')])
        ret = False
        if matching_reports:
            report = ir_actions_report.browse(cr, uid, matching_reports[0])
            report_service = 'report.' + report.report_name
            service = netsvc.LocalService(report_service)
            (result, format) = service.create(cr, uid, [record.id], {'model': self._name}, context=context)
            eval_context = {'time': time, 'object': record}
            if not report.attachment or not eval(report.attachment, eval_context):
                # no auto-saving of report as attachment, need to do it manually
                result = base64.b64encode(result)
                file_name = record.name_get()[0][1]
                file_name = re.sub(r'[^a-zA-Z0-9_-]', '_', file_name)
                file_name += ".pdf"
                ir_attachment = self.pool.get('ir.attachment').create(cr, uid,
                                                                      {'name': file_name,
                                                                       'datas': result,
                                                                       'datas_fname': file_name,
                                                                       'res_model': self._name,
                                                                       'res_id': record.id},
                                                                      context=context)
                ret = ir_attachment
        return ret
    
    #override to force creation of pdf report (base function (ir.actions.server) was unlinked and replaced by this one)
    def action_number(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).action_number(cr, uid, ids, context)
        for inv in self.browse(cr, uid, ids, context):
            report_attach = self._create_report_attach(cr, uid, inv, context)
        return res
    
account_invoice()
    
    
