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
from datetime import datetime

from osv import fields, osv
import netsvc
from tools.translate import _

#----------------------------------------------------------
# Fournitures
#----------------------------------------------------------
class product_product(osv.osv):
    def _calc_qte_dispo_now(self, cr, uid, ids, name, args, context=None):
        print("début calcul dispo")
        print(ids)
        if not isinstance(ids, list):
            ids = [ids]
        #Pour cela, on regarde toutes les réservations de produits qui sont prévues ou à prévoir durant aujourd'hui
        aujourdhui = datetime.now()
        debut = aujourdhui.replace(hour=0, minute=0, second=0)
        fin = aujourdhui.replace(hour=23, minute=59, second=59)
        print(str(debut)) 
        print(str(fin))
        ret = {}
        stock_prod = self._product_available(cr, uid, ids, ['qty_available'])
        #Par défaut, on indique la qté max pour chaque produit
        for id in ids:
            ret[id] = stock_prod[id]['qty_available']
        #Puis pour les articles réservés, on en retranche le nombre réservés 
        for r in self.pool.get("hotel.reservation").get_nb_prod_reserved(cr, ids, str(debut), str(fin)).fetchall():
            qte_total_prod = stock_prod[r[0]]['qty_available']
            qte_reservee = r[1]
            ret[r[0]] = qte_total_prod - qte_reservee
        print(ret)
        return ret
    
    AVAILABLE_ETATS = (("neuf", "Neuf"), ("bon", "Bon"), ("moyen", "Moyen"), ("mauvais", "Mauvais"), ("inutilisable", "Inutilisable"))

    _name = "product.product"
    _inherit = "product.product"
    _description = "Task Category"
    _columns = {
        "qte_dispo": fields.function(_calc_qte_dispo_now, store=True,string="Disponible Aujourd'hui", type="integer", readonly=True),
        "geo": fields.char("Position Géographique", 128),
        "etat": fields.selection(AVAILABLE_ETATS, "Etat"),
        "seuil_confirm":fields.integer("Qté Max sans Validation", help="Qté Maximale avant laquelle une étape de validation par un responsable est nécessaire"),
        }

    _defaults = {
        'isroom': lambda *a: 1,
        'seuil_confirm': 0,
    }

product_product()

class hotel_reservation_line(osv.osv):
    _name = "hotel_reservation.line"
    _inherit = "hotel_reservation.line"
    _columns = {
        'categ_id': fields.many2one('product.category','Type d\'article'),
        "reserve_product": fields.many2one("product.product", "Articles réservés"),
        "qte_reserves":fields.integer("Quantité désirée"),
        "prix_unitaire": fields.float("Prix Unitaire", digit=(3,2)),
        "dispo":fields.boolean("Disponible")
        }

hotel_reservation_line()

class hotel_reservation(osv.osv):
    _name = "hotel.reservation"
    _inherit = "hotel.reservation"
    _description = "Réservations"

    _columns = {
                'state': fields.selection([('draft', 'A Valider'),('confirm','Confirmée'),('cancle','Annulée'),('in_use','En cours d\'utilisation'),('done','Terminée'), ('remplir','Brouillon')], 'Etat',readonly=True),
                'in_option':fields.boolean("En Option", readonly = True, help=("""Une réservation en option signifie 
                que votre demande est prise en compte mais qu'un ou plusieurs articles que vous voulez réserver ne 
                sont pas disponible à cette date.""")),
                'name':fields.char('Nom Manifestation', size=128),
                'partner_mail':fields.char('Email Demandeur', size=128, required=False)
        }
    _defaults = {
                 'in_option': lambda *a :0,
                 'state': lambda *a: 'remplir'
        }
    _order = "checkin, in_option"

    def confirmed_reservation(self,cr,uid,ids):
        #self.write(cr, uid, ids, {'state':'confirm'})
        if self.is_all_dispo(cr, uid, ids[0]):
            self.write(cr, uid, ids, {'state':'confirm'}, context={'check_dispo':'1'})
            #TODO: Envoi mail d'info au demandeur : Demande prise en compte mais doit être validée
            return True
        else:
            raise osv.except_osv("""Vous devez vérifier les disponibilités""","""Erreur de validation du formulaire: un ou plusieurs
             de vos articles ne sont pas disponibles, ou leur disponibilité n'a pas encore été vérifiée. 
             Vous devez valider les disponibilités de vos articles via le bouton "vérifier disponibilités".""")
            return False
        return True
    
    #Mettre à l'état cancle et retirer les mouvements de stocks (supprimer mouvement ou faire le mouvement inverse ?)
    def cancelled_reservation(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state':'cancle', 'in_option':False})
        self.envoyer_mail(cr, uid, ids, {"to":"","state":"error"})
        return True
    
    
    def drafted_reservation(self, cr, uid, ids):
        if self.is_all_dispo(cr, uid, ids[0]):
            self.write(cr, uid, ids, {'state':'draft'}, context={'check_dispo':'1'})
            #TODO: Envoi mail d'info au demandeur : Demande prise en compte mais doit être validée
            return True
        else:
            raise osv.except_osv("""Vous devez vérifier les disponibilités""","""Erreur de validation du formulaire: un ou plusieurs
             de vos articles ne sont pas disponibles, ou leur disponibilité n'a pas encore été vérifiée. 
             Vous devez valider les disponibilités de vos articles via le bouton "vérifier disponibilités".""")
            return False
    
    def redrafted_reservation(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state':'remplir'})
        return True
    def in_used_reservation(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state':'in_use'})
        return True
    def done_reservation(self, cr, uid, ids):
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
        #TODO: Rajouter le test sur res.group => si responsable(s) (à définir lesquels), renvoyer False
        reservations = self.browse(cr, uid, ids)
        #if group <> "Responsable":
        etape_validation = False
        for resa in reservations:
            for line in resa.reservation_line:
                if line.qte_reserves > line.reserve_product.seuil_confirm:
                    etape_validation = True
        print("need_confirm")
        print(etape_validation)
        return etape_validation
    
    def not_need_confirm(self, cr, uid, ids):
        return not self.need_confirm(cr, uid, ids)
    
    def ARemplir_reservation(self, cr, uid, ids):
        #TOCHECK: Voir quand il faut mettre la résa à l'état "in_option" : Clique sur Suivant malgré non dispo ?
        self.write(cr, uid, ids, {'state':'remplir', 'reservation_line':self.uncheck_all_dispo(cr, uid, ids)})
        return True
    
    #Cette fonction déclenche le signal "reserv_modified" du wkf pour indiquer qu'il faut refaire 
    #l'étape de validation de dispo (on revient à l'état "A Remplir" Pour valider les modifs.
    def trigger_reserv_modified(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        for id in ids:
            wf_service.trg_validate(uid, 'hotel.reservation', id, 'reserv_modified', cr)
        return
    
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
    
    def get_nb_prod_reserved(self, cr, prod_list, checkin, checkout, where_optionnel=""):
        print("début get_nb_prod_reserved")
        cr.execute("select reserve_product, sum(qte_reserves) as qte_reservee \
                    from hotel_reservation as hr, \
                    hotel_reservation_line as hrl \
                    where hr.id = hrl.line_id \
                    and reserve_product in %s \
                    and hr.state not in('cancle', 'done') \
                    and (hr.checkin, hr.checkout) overlaps ( timestamp %s, timestamp %s ) \
                    " + where_optionnel + " \
                    group by reserve_product; ", (tuple(prod_list), checkin, checkout))
        return cr
    
    def check_dispo(self, cr, uid, id=0, context=None):
        reservation = self.browse(cr, uid, id)
        if isinstance(reservation, list):
            reservation = reservation[0]
        where_optionnel = " and hr.id <> " + str(id)
        checkin = reservation.checkin
        checkout = reservation.checkout
        reserv_vals = reservation.reservation_line
        demande_prod = {}
        prod_list = []
        prod_list_all = []
        #Parcours des lignes de réservation pour 
        for line in reserv_vals:
            #Récup des produits à réserver
            prod_list.append(line.reserve_product.id)
            prod_list_all.append(line.reserve_product.id)
            demande_prod[str(line.reserve_product.id)] = line.qte_reserves
        
        print(reserv_vals)
        
        #Vérif dispo pour chaque produit
        ok = True
        #On vérifie que l'on a récupéré au moins un produit
        #Dictionnaire des qtés totales de chaque produit de la demande en cours
        stock_prod = self.pool.get("product.product")._product_available(cr, uid, prod_list, ['qty_available'])
        #Liste des produits non disponibles
        print(stock_prod)
        dict_error_prod = {}
        #NOTES:chaque produit que l'on récupère de la requête sql indique que ce produit a été loué au moins une fois
        #Ainsi, si un produit figure dans la demande en cours mais non présent dans le résultat sql, c'est qu'on n'a jamais réservé ce produit
        results = self.get_nb_prod_reserved(cr, prod_list, checkin, checkout, where_optionnel).fetchall()
        print(results)
        ok = results and ok or False
        print(ok)
        #Vérif dispo : Cas d'un produit déjà loué
        for data in results:
            #prod_desire = self.pool.get("product.product").browse(cr, uid, data[1])
            #print(prod_desire)
            qte_total_prod = stock_prod[data[0]]['qty_available']
            qte_voulue = demande_prod[str(data[0])]
            #Si l'un des produits n'est pas dispo, on annule la réservation des articles
            #TOCHECK:la réservation reste à l'état draft 
            #on vérifie si le produit est dispo en quantité suffisante : stock total - qtés déjà résevées - qtés voulues
            if qte_total_prod < data[1] + qte_voulue:
                ok = False
                dict_error_prod[data[0]] = [qte_voulue, data[1]]
            prod_list.remove(data[0])
        #Vérif dispo : Cas où on réserve un produit pour la première fois, autrement dit, s'il reste des occurences dans prod_list
        for prod_id in prod_list:
             ok = True
             qte_total_prod = stock_prod[prod_id]['qty_available']
             qte_voulue = demande_prod[str(prod_id)]
             if qte_total_prod < qte_voulue:
                 ok = False
                 dict_error_prod[prod_id] = [qte_voulue, qte_total_prod]
        print(ok)
        #Si on a cliqué sur "vérifier dispo", on fait seulement un update des lignes de résa sur le champs dispo
        if 'update_line_dispo' in context:    
            line_prod_ids_dispo = self.pool.get("hotel_reservation.line").search(cr, uid, [('line_id', '=',id),('reserve_product','in',prod_list_all)])
            print (line_prod_ids_dispo)
            line_prod_ids_non_dispo = self.pool.get("hotel_reservation.line").search(cr, uid, [('line_id', '=',id),('reserve_product','in',dict_error_prod.keys())])
            print(line_prod_ids_non_dispo)
            
            list_for_update = []
            #Par défaut tous les produits sont dispo
            for line_id in line_prod_ids_dispo:
                list_for_update.append((1, line_id,{'dispo':True},))
            print(list_for_update)
            if list_for_update:    
                self.write(cr, uid, [id], {'reservation_line':list_for_update})
                
            list_for_update = []
            #Et on mets à jour les lignes dont le produit n'est pas dispo
            for line_id in line_prod_ids_non_dispo:
                list_for_update.append((1, line_id,{'dispo':False}),)
            print(list_for_update)
            if list_for_update:
                self.write(cr, uid, [id], {'reservation_line':list_for_update})
                        
        if not ok:
            prod_error_str = ""
            for prod_error in self.pool.get("product.product").browse(cr, uid, dict_error_prod.keys()):
                if prod_error_str <> "":
                    prod_error_str +=", "
                prod_error_str += str(dict_error_prod[prod_error.id][0]) + " x " + prod_error.name + "( " + str(dict_error_prod[prod_error.id][1]) + " disponibles pour ces dates)"
            if not 'update_line_dispo' in context:
                raise osv.except_osv("Produit(s) non disponible(s)","Votre réservation n'a pas aboutie car \
                les produits suivants ne sont disponibles pour la période " + checkin + " - " + checkout + ":\
                " + prod_error_str)
        return dict_error_prod
    
    #Bouton pour vérif résa, mets à jour les champs dispo de chaque ligne de résa
    def verif_dispo(self,cr ,uid, ids, context=None):
        context['update_line_dispo'] = 1
        list_prod_error = {}
        ok = True
        for id in ids:
            list_prod_error = self.check_dispo(cr, uid, id, context)
            if list_prod_error:
                ok = False
        #S'il y a une erreur de dispo, on affichage une wizard donnant accès à l'action d'emprunt des articles
        if not ok:
           ret = {'view_mode':'form',
                   'res_model':'openstc.pret.warning.dispo.wizard',
                   'type':'ir.actions.act_window',
                   'context':{'prod_error_ids':list_prod_error,
                              'reservation_id':id},
                  'target':'new',
                  }
            
           return ret
        #S'il n'y a pas d'erreurs dans la réservation, on poursuit le processus normal
        return {'view_mode': 'form,tree',
                'res_model': 'hotel.reservation',
                'type': 'ir.actions.act_window',
                'res_id':ids[0]
                }
        
    #Vérifies les champs dispo de chaque ligne de résa pour dire si oui ou non la résa est OK pour la suite
    #TODO: Voir comment gérer le cas de la reprise d'une résa à revalider / incomplète où des champs dispo sont à True
    #=> Problème lorsque quelqu'un d'autre réserve un même produit
    def is_all_dispo(self, cr, uid, id, context=None):
        for line in self.browse(cr, uid, id, context).reservation_line:
            if not line.dispo:
                return False
        return True
    
    #Renvoies actions bdd permettant de mettre toutes les dispo de la résa à False
    #Ne renvoie que les actions de mises à jours des lignes déjà enregistrées dans la réservation
    def uncheck_all_dispo(self, cr, uid, ids, contex=None):
        line_ids = self.pool.get("hotel_reservation.line").search(cr, uid, [('line_id','in',ids)])
        reservation_line = []
        for line in line_ids:
            reservation_line.append((1,line,{'dispo':False}))
        return reservation_line
    
    #Lors de l'appui sur le bouton "Générer Check-In", on créé le checkin et on passe l'état de la résa à in_use
    def do_checkin(self, cr, uid, ids, context=None):
        for reservation in self.browse(cr,uid,ids):
            for line in reservation.reservation_line:
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
                                                                  'room_lines': [(0,0,{'folio_id':line['id'],
                                                                                       'checkin_date':reservation['checkin'],
                                                                                       'checkout_date':reservation['checkout'],
                                                                                       'product_id':line.reserve_product.id,
                                                                                       'name':reservation['reservation_no'],
                                                                                       'product_uom':line.reserve_product.uom_id.id,
                                                                                       'price_unit':line.reserve_product.lst_price,
                                                                                       'product_uom_qty':line.qte_reserves

                                                                                       })],
                                                                   })
                cr.execute('insert into hotel_folio_reservation_rel (order_id,invoice_id) values (%s,%s)', (reservation.id, folio))
        wf_service = netsvc.LocalService('workflow')
        if folio and folio > 0:
            for id in ids:
                wf_service.trg_validate(uid, 'hotel.reservation', id, 'put_in_use', cr)
        return {
                'view_mode': 'form,tree',
                'res_model': 'hotel.folio',
                'type': 'ir.actions.act_window',
                'res_id':folio,
                'target':'new'
                }
    #Vals: Dict containing "to" (required) and "state" in ("error","draft", "confirm") (required)
    def envoyer_mail(self, cr, uid, ids, vals=None, context=None):
        #TOREMOVE: A déplacer vers un fichier init.xml
        #Si le modèle n'existe pas, on le crée à la volée
        email_obj = self.pool.get("email.template")
        email_tmpl_id = 0
        print(vals)
        if ('to' or 'state') in vals.keys() and vals['state'] == "error":
            print("envoyer mail pour résa annulée")
            email_tmpl_id = email_obj.search(cr, uid, [('model','=',self._name),('name','ilike','annulée')])
            if not email_tmpl_id:
                print("création email_template pour résa annulée")
                ir_model = self.pool.get("ir.model").search(cr, uid, [('model','=',self._name)])
                email_tmpl_id = email_obj.create(cr, uid, {
                                            'name':'modèle de mail pour résa annulée', 
                                            'name':'Réservation Annulée',
                                            'model_id':ir_model[0],
                                            'subject':'Votre Réservation du ${object.checkin.strftime("%d")} au ${object.checkout} a été annulée',
                                            'email_from':'bruno.plancher@gmail.com',
                                            'email_to':'bruno.plancher@gmail.com',
                                            'body_text':"""Votre Réservation normalement prévue du ${object.checkin} au 
                                            ${object.checkout} dans le cadre de votre manifestation : ${object.name} a été annulée,
                                            pour plus d'informations, veuillez contacter la mairie de Pont L'abbé au : 0240xxxxxx \n 
                                            """,
                                            'body_html':"""Votre Réservation normalement prévue du ${object.checkin} au 
                                            ${object.checkout} dans le cadre de votre manifestation : ${object.name} a été annulée, 
                                            pour plus d'informations, veuillez contacter la mairie de Pont L'abbé au : 0240xxxxxx </br>
                                            """
                                           })
            else:
                email_tmpl_id = email_tmpl_id[0]
        
        #Envoi du mail proprement dit, email_tmpl_id définit quel mail sera envoyé
        print(email_tmpl_id)
        print(ids)
        for id in ids:
            email_obj.send_mail(cr, uid, email_tmpl_id, id)
        return
         
    def create(self, cr, uid, vals, context=None):
        #Si on vient de créer une nouvelle réservation et qu'on veut la sauvegarder (cas où l'on appuie sur
        #"vérifier disponibilités" juste après la création (openERP force la sauvegarde)
        #Dans ce cas, on mets des valeurs par défauts pour les champs obligatoires
        print(vals)
        if not 'state' in vals or vals['state'] == 'remplir':
            vals['shop_id'] = self.pool.get("sale.shop").search(cr, uid, [], limit=1)[0]
            vals['partner_id'] = self.pool.get("res.partner").search(cr, uid, [], limit=1)[0]
            part_vals = self.onchange_partner_id( cr, uid, [], vals['partner_id'])
            for (cle, data) in part_vals['value'].items():        
                vals[cle] = data
        #id = super(hotel_reservation, self).create(cr, uid, vals, context)        
        return super(hotel_reservation, self).create(cr, uid, vals, context)
        #TOCHECK: Vérif utilité, supprimer puis tester si tout fonctionne
        """else:
            id = super(hotel_reservation, self).create(cr, uid, vals, context)
            
            try:
                self.check_dispo(cr, uid, id, context)
            except osv.except_osv as e:
                self.write(cr, uid, id, {'in_option':True})
        if id:
            print("affichage message")
            self.log(cr, uid, id, "Réservation enregistrée")
        return id"""
    
    def write(self, cr, uid, ids, vals, context=None):
        #OpenERP fait toujours un write des modifs faites sur le form lors d'un clic de bouton, ce qui peut 
        #conduire à un write(cr, uid, ids, {})
        print(vals)
        print(context)
        return super(hotel_reservation, self).write(cr, uid, ids, vals, context)
    
    def unlink(self, cr, uid, ids, context):
        #renvoi des articles dans le stock
        return super(hotel_reservation, self).unlink(cr, uid, ids, context)
    
    def onchange_in_option(self, cr, uid, ids, in_option=False, state=False, context=None):
        #if in_option:
            #Affichage d'un wizard pour simuler une msgbox
        print('on_change_in_option')
        print(state)
        if state and state in ('draft','confirm'):
            return {'warning':{'title':'Réservation mise en option', 'message': 'Attention, certains produits ne sont pas disponibles, votre réservation est mise en option.'}}
        
        return {'value':{}}
    
    def on_change_checkout(self, cr, uid, ids, checkin=False, checkout=False, state=False, reservation_line = False, context=None):
        print("on_change_checkout")
        print(state)
        ret = super(hotel_reservation, self).on_change_checkout(cr, uid, ids, checkin, checkout, context)
        print(ids)
        #TODO: Permet d'enregistrer les lignes de réservations lors d'un onchange
        """if reservation_line and ids:
            self.write(cr, uid, ids, {'reservation_line':reservation_line})"""
        #Fin TOCHECK
        
        if state and state in ('confirm','draft'):
            #TODO: Mettre la mise à l'état "remplir" dans le wkf, peut-être via une activité intermédiaire
            self.trigger_reserv_modified(cr, uid, ids, context)
            if ids:
                #ret['value'] = {'state':'remplir', 'reservation_line': self.uncheck_all_dispo(cr, uid, ids, context)}
                ret['value'] = {'state':'remplir'}
            ret['warning'] = {'title':'Modification(s) importante(s) de la réservation', 'message':"""Les modifications de la réservation (ajout/modification 
                                   d\'articles réservés ou des dates de réservation) impliquent de revalider la disponibilité des articles que vous
                                   souhaitez réserver. Veuillez cliquer à nouveau sur le bouton "Vérifier Disponibilités"."""}
        
        if state and state in ("remplir","draft","confirm"):
            if not reservation_line:
                reservation_line = []
            reservation_line.extend(self.uncheck_all_dispo(cr, uid, ids, context))
            ret.update({'reservation_line':reservation_line})
        return ret
        
    def on_change_reservation_line(self, cr ,uid, ids, reservation_line=False, state=False, context=None):
        ret = {'value':{}}
        """if reservation_line and ids:
            self.write(cr, uid, ids, {'reservation_line':reservation_line})"""
        if state and state in ('draft', 'confirm'):
            for data in reservation_line:
                #Toute modif de lignes produits entraîne une revalidation, seule la suppression d'une ligne outrepasse cette étape
                #si aucune modif n'implique de re-valider les dispo, on laisse l'utilisateur poursuivre
                if data[0] <> 4:
                    self.trigger_reserv_modified(cr, uid, ids, context)
                    ret['value'] = 'remplir'
                    if not reservation_line:
                        reservation_line = []
                    reservation_line.extend(self.uncheck_all_dispo(cr, uid, ids, context))
                    ret['value'] = {'reservation_line': reservation_line}
                    ret['warning'] = {'title':'Modification(s) importante(s) de la réservation', 'message': """Les modifications de la réservation (ajout/modification 
                                d\'articles réservés ou des dates de réservation) impliquent de revalider la disponibilité des articles que vous
                                souhaitez réserver. Veuillez cliquer à nouveau sur le bouton "Vérifier Disponibilités"."""}
                    break
        return ret
    
    def onchange_partner_id(self, cr, uid, ids, part):
        vals = super(hotel_reservation, self).onchange_partner_id(cr, uid, ids, part)
        print(vals)
        if part:
            print("partner_id is not NULL")
            print(part)
            vals['value']['partner_mail'] = self.pool.get("res.partner.address").browse(cr, uid, vals['value']['partner_invoice_id']).email
        print(vals)
        return vals
    
hotel_reservation()

class hotel_folio(osv.osv):
    _inherit = "hotel.folio"
    _name = "hotel.folio"
    _order = "checkout_date desc"
    
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
