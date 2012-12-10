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
from osv import fields, osv
import netsvc
from datetime import datetime
#
#Wizard permettant d'emprunter des ressources à des collectivités extérieures
#

class openstc_pret_emprunt_wizard(osv.osv_memory):
    
    _name = 'openstc.pret.emprunt.wizard'
    
    _rec_name = 'date_start'
    _columns = {
                'emprunt_line':fields.one2many('openstc.pret.emprunt.line.wizard','line_id',string="Lignes d'emprunt"),
                'origin':fields.char('Document d\'origine', size=32)
                }
    
    
    def default_get(self, cr, uid, fields, context=None):
        ret = super(openstc_pret_emprunt_wizard, self).default_get(cr, uid, fields, context)
        #Valeurs permettant d'initialiser les lignes d'emprunts en fonction des lignes de réservation de la résa source
        print(context)
        emprunt_values = []
        if context and ('reservation_id' and 'prod_error_ids') in context:
            print(context['prod_error_ids'])
            dict_error_prods = context['prod_error_ids']
            resa = self.pool.get("hotel.reservation").browse(cr, uid, context['reservation_id'])
            ret['origin'] = resa.reservation_no
            for line in resa.reservation_line:
                #TODO: dans openstock.py (check_dispo function) mettre les clés de dict_error_prod en integer (et non str)
                if str(line.reserve_product.id) in dict_error_prods.keys():
                    #List contenant le résultat d'une requête sql calculée dans openstock.py renvoyant [qte_voulue, qte_dispo]
                    prod_error = dict_error_prods[str(line.reserve_product.id)]
                    if line.reserve_product.empruntable:
                        emprunt_values.append((0,0,{'product_id':line.reserve_product.id,
                                                    'qte': prod_error[0] - prod_error[1],
                                                    'price_unit':line.prix_unitaire}))
            ret.update({'emprunt_line' : emprunt_values})
            print(ret)
        return ret
    
    def do_emprunt(self,cr,uid,ids,context=None):
        
        if context is None:
            context = {}
        #Dict contenant les lignes "d'achat" pour chaque fournisseur
        dict_partner = {}
        #Initialisation d'objets et de records utiles pour la création de bons de commandes
        purchase_obj = self.pool.get("purchase.order")
        #TODO: Faire une fonction globale pour récupérer l'emplacement "stock" interne (au cas où le nom changerait)
        default_location_id = self.pool.get("stock.location").search(cr, uid, [('name','=','Stock')])[0]
        origin = ""
        for emprunt in self.browse(cr, uid, ids):
            origin = emprunt.origin
            for line in emprunt.emprunt_line:
                line_values = [(0,0,{
                                    'product_id':line.product_id.id, 
                                    'product_qty':line.qte, 
                                    'date_planned':line.date_expected,
                                    'price_unit':line.price_unit,
                                    'name':'emprunt: ' + line.product_id.name_template,
                                    'date_planned':line.date_expected or datetime.now()})]
                if line.partner_id.id in dict_partner.keys():
                    dict_partner[line.partner_id.id].extend(line_values)
                else:
                    dict_partner[line.partner_id.id] = line_values
        
        #Pour chaque mairie (fournisseur), on crée un bon de commande
        for (partner_id, purchase_lines) in dict_partner.items():
            #Dict qui Contient tous les éléments pour créer un nouveau bon de commande
            values = {'invoice_method':'manual',
                      'location_id':default_location_id,
                      'partner_id':partner_id,
                      'order_line':purchase_lines,
                      'origin': origin,
                      'is_emprunt':True,
                      }
            #On insère les modifs de l'onchange sur partner_id pour compléter les champs obligatoires
            for (key, value) in purchase_obj.onchange_partner_id(cr, uid, False, partner_id)['value'].items():
                values[key] = value
            
            print(values)      
            purchase_id = purchase_obj.create(cr, uid, values)
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'purchase.order', purchase_id, 'purchase_confirm', cr)
        #TODO: Nettoyer le context des valeurs personnalisées comme reservation_id ou prod_error_ids après exécution
        return self.pool.get("hotel.reservation").verif_dispo(cr, uid, [context['reservation_id']], context)

openstc_pret_emprunt_wizard()

class openstc_pret_emprunt_line_wizard(osv.osv_memory):
    _name="openstc.pret.emprunt.line.wizard"
    _columns={
              'line_id':fields.many2one('openstc.pret.emprunt.wizard', required=True),
              'product_id':fields.many2one('product.product', string="Ressource à Emprunter", required=True),
              'partner_id':fields.many2one('res.partner', string="Collectivité prêtant", required=True),
              'qte':fields.integer('Quantité empruntée', required=True),
              'price_unit':fields.float('Prix Unitaire', digit=(4,2)),
              'date_expected':fields.date('Date de livraison')
              }
    _order= "product_id"
    _default={
              'price_unit':0,
              'date_expected':fields.date.context_today
              }
openstc_pret_emprunt_line_wizard()

class openstc_pret_warning_no_wizard(osv.osv_memory): 
    _name = "openstc.pret.warning.dispo.wizard"
    _columns={
              }

openstc_pret_warning_no_wizard()


class openstc_pret_envoie_mail_annulation_wizard(osv.osv_memory):
    _name = 'openstc.pret.envoie.mail.annulation.wizard'
    _columns = {
                'body_html':fields.text("Message du mail notifiant l'annulation"),
                'email_template':fields.many2one('email.template','Modèle d\'Email')
                }
    
    def default_get(self, cr, uid, fields, context=None):
        ret = super(openstc_pret_envoie_mail_annulation_wizard, self).default_get(cr, uid, fields, context)
        #Générer mail pré-rempli, selon email.template
        #TOREMOVE: A déplacer vers un fichier init.xml
        #Si le modèle n'existe pas, on le crée à la volée
        id = context['active_id']
        email_obj = self.pool.get("email.template")
        email_tmpl_id = 0
        print("envoyer mail pour résa annulée")
        email_tmpl_id = email_obj.search(cr, uid, [('model','=','hotel.reservation'),('name','ilike','annulée')])
        if not email_tmpl_id:
            print("création email_template pour résa annulée")
            ir_model = self.pool.get("ir.model").search(cr, uid, [('model','=','hotel.reservation')])
            email_tmpl_id = email_obj.create(cr, uid, {
                                        'name':'modèle de mail pour résa annulée', 
                                        'name':'Réservation Annulée',
                                        'model_id':ir_model[0],
                                        'subject':'Votre Réservation du ${object.checkin} au ${object.checkout} a été annulée',
                                        'email_from':'bruno.plancher@gmail.com',
                                        'email_to':'bruno.plancher@gmail.com',
                                        'body_text':"Votre Réservation normalement prévue du ${object.checkin} au \
                                        ${object.checkout} dans le cadre de votre manifestation : ${object.name} a été annulée,\
                                        pour plus d'informations, veuillez contacter la mairie de Pont L'abbé au : 0240xxxxxx",
                                        'body_html':"Votre Réservation normalement prévue du ${object.checkin} au \
                                        ${object.checkout} dans le cadre de votre manifestation : ${object.name} a été annulée,\
                                        pour plus d'informations, veuillez contacter la mairie de Pont L'abbé au : 0240xxxxxx"
                                       })
        else:
            email_tmpl_id = email_tmpl_id[0]
        mail_values = email_obj.generate_email(cr, uid, email_tmpl_id, id, context)
        #TODO: ajouter les attachments au mail, voir sources de email.message
        attachments = mail_values.pop('attachments') or {}
        ret['body_html'] = mail_values['body_html']
        ret['email_template'] = email_tmpl_id
        return ret

    #Bouton Pour Annuler Résa : Affiche le mail pré-rempli à envoyer à l'association pour signifier l'annulation
    def do_cancel(self, cr, uid, ids, context=None):
        if isinstance(ids, list):
            ids = ids[0]
        wizard = self.browse(cr, uid, ids)
        mail_id = self.pool.get("email.template").send_mail(cr, uid, wizard.email_template, context['active_id'], False, context)
        self.pool.get("mail.message").write(cr, uid, mail_id, {'body_html':wizard.body_html})
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'hotel.reservation', context['active_id'], 'cancel', cr)
            
        return {
                'type':'ir.actions.act_window_close'
                }
    #TODO: Rajouter contrôle sur active_model dans context
    def do_cancel_without_mail(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'hotel.reservation', context['active_id'], 'cancel', cr)
            
        return {
                'type':'ir.actions.act_window_close'
                }
    
openstc_pret_envoie_mail_annulation_wizard()