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
from tools.translate import _
from mx.DateTime.mxDateTime import strptime
import pytz

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
        prod_ctx = {}
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
                                                    'qty_needed':prod_error[0] - prod_error[1],
                                                    'price_unit':line.prix_unitaire}))
                        prod_ctx.setdefault(line.reserve_product.id,prod_error[0] - prod_error[1])
            context.update({'prod_ctx':prod_ctx})
            ret.update({'emprunt_line' : emprunt_values})
            print(ret)
        return ret
    
    def prepare_sale_order(self, cr, uid, default_location_id, partner_id, purchase_lines, origin=False):
        return {'invoice_method':'manual',
                      'location_id':default_location_id,
                      'partner_id':partner_id,
                      'order_line':purchase_lines,
                      'origin': origin or '',
                      'is_emprunt':True,
                      }
    
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
     
            values = self.prepare_sale_order(cr, uid, default_location_id, partner_id, purchase_lines, origin)
            #On insère les modifs de l'onchange sur partner_id pour compléter les champs obligatoires
            for (key, value) in purchase_obj.onchange_partner_id(cr, uid, False, partner_id)['value'].items():
                values[key] = value
               
            purchase_id = purchase_obj.create(cr, uid, values)
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'purchase.order', purchase_id, 'purchase_confirm', cr)
        #TODO: Nettoyer le context des valeurs personnalisées comme reservation_id ou prod_error_ids après exécution
        return self.pool.get("hotel.reservation").verif_dispo(cr, uid, [context['reservation_id']], context)


    def onchange_emprunt_line(self, cr, uid, ids, emprunt_line=False, context=None):
        ret_values = []
        if emprunt_line:
            prod_ctx = {}
            #gets qty planned and qty needed by prod
            for item in emprunt_line:
                if item[0] == 0 or item[0] == 1:
                    prod_ctx.setdefault(item[2]['product_id'],{'qte':0,'qty_needed':item[2]['qty_needed'],'partner_id':item[2].get('partner_id',False)})
                    prod_ctx[item[2]['product_id']]['qte'] += item[2]['qte']
            for key, values in prod_ctx.items():
                #create new lines to complete 'emprunt'
                if values['qte'] < values['qty_needed']:
                    #ret_values.append({'product_id':key, 'qte':values['qty_needed'] - values['qte'], 'qty_needed':values['qty_needed']})
                    ret_values.append((0,False,{'product_id':key, 'qte':values['qty_needed'] - values['qte'], 'qty_needed':values['qty_needed'], 'partner_id':values['partner_id']}))
                    
        emprunt_line.extend(ret_values)
        return {'value':{'emprunt_line':emprunt_line}}

openstc_pret_emprunt_wizard()

class openstc_pret_emprunt_line_wizard(osv.osv_memory):
    _name="openstc.pret.emprunt.line.wizard"
    _columns={
              'line_id':fields.many2one('openstc.pret.emprunt.wizard'),
              'product_id':fields.many2one('product.product', string="Ressource à Emprunter", required=True),
              'partner_id':fields.many2one('res.partner', string="Collectivité prêtant", required=True),
              'qte':fields.integer('Quantité empruntée', required=True),
              'qty_needed':fields.integer('Quantité Minimale nécessaire pour la réservation', required=True, readonly=True),
              'price_unit':fields.float('Prix Unitaire', digit=(4,2)),
              'date_expected':fields.date('Date de livraison'),
              }
    _order= "product_id"
    _default={
              'price_unit':0,
              'date_expected':fields.date.context_today
              }

    def create(self, cr, uid, vals, context=None):
        res = super(openstc_pret_emprunt_line_wizard, self).create(cr, uid, vals, context=context)
        return res
"""    def onchange_qte(self, cr, uid, ids, qte=False,qty_needed=False,product_id=False,context=None):
        values_onchange = {}
        values = {}
        if qte and qty_needed and product_id:
            if qte < qty_needed:
                values.update({'product_id':product_id,'qte':qty_needed - qte, 'qty_needed':qty_needed - qte})
                values_onchange.update({'qty_needed':qte})
            elif qte > qty_needed:
                values_onchange.update({'qty_needed':qte})
        #context.update({'emprunt_line':values})
        values_onchange.update({'context_emprunt_line':str(values)})
        return {'value':values_onchange}
    
    def default_get(self, cr, uid, fields, context=None):
        if 'emprunt_line' in context:
            #if len(context['emprunt_line']) >= 1:
            return context['emprunt_line']
        return {}"""
    
openstc_pret_emprunt_line_wizard()


class openstc_pret_warning_dispo_wizard(osv.osv_memory):
    _name = "openstc.pret.warning.dispo.wizard"
    
    def view_planning(self, cr, uid, ids, context=None):
        if 'all_prods' in context:
            return {
                'type':'ir.actions.act_window',
                'view_type':'form',
                'view_mode':'calendar,tree,form',
                'domain':[('reservation_line.reserve_product','in',context['all_prods'])],
                'target':'new',
                'res_model':'hotel.reservation',
                }
        return osv.except_osv("Erreur","OpenSTC A perdu la référence des ressources A afficher, veuillez re-cliquer sur vérif dispo A partir du formulaire de réservation.")
    
openstc_pret_warning_dispo_wizard()


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

#Pop-up permettant de savoir si, pour mettre à disposition les articles, on fait une livraison ou le demandeur vient les chercher
class openstc_pret_deliver_products_wizard(osv.osv_memory):
    _name = "openstc.pret.deliver.products.wizard"
    _columns = {
                'deliver_line':fields.one2many('openstc.pret.deliver.products.line.wizard','wizard_id','Interventions A Générer'),
                }
    
    def default_get(self, cr, uid, field_names, context=None):
        if 'active_id' in context:
            line_values = []
            resa = self.pool.get("hotel.reservation").browse(cr, uid, context['active_id'])
            #prepare supply intervention
            service_id = self.pool.get("openstc.service").search(cr, uid, [('name','like','Voirie')])
            if isinstance(service_id, list):
                service_id = service_id[0]
            line_values.append({'to_generate':True, 'service_id':service_id,'motif':'supply', 'site_details':''.join(_(x.reserve_product.name_template + ' : ' + x.infos) for x in resa.reservation_line if x.infos)})
            #prepare technical interventions if needed
            for line in resa.reservation_line:
                if line.reserve_product.service_technical_id:
                    line_values.append({'service_id':line.reserve_product.service_technical_id.id,
                                        'motif':'technical',
                                        'site_details':line.infos,
                                        'product_id':line.reserve_product.id,
                                        'to_generate':True,
                                        'qte_reserves':line.qte_reserves})
        return {'deliver_line':[(0,0,x) for x in line_values]}
    
    #Résa mise à "en cours d'utilisation" avec création d'une intervention
    def put_in_use_with_intervention(self, cr, uid, ids, context=None):
        if 'active_id' in context:
            resa = self.pool.get("hotel.reservation").browse(cr, uid, context['active_id'])
            if isinstance(ids, list):
                ids = ids[0]
            wizard = self.browse(cr, uid, ids, context)
            lines = [x for x in wizard.deliver_line if x.to_generate]
            #Générer intervention de livraison et interventions optionnelles
            checkin = datetime.strptime(resa.checkin, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
            checkout = datetime.strptime(resa.checkout, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
            checkin_str = checkin.astimezone(pytz.timezone('Europe/Paris')).strftime('%x à %H:%M')
            checkout_str = checkout.astimezone(pytz.timezone('Europe/Paris')).strftime('%x à %H:%M')
            user = self.pool.get("res.users").browse(cr, uid, uid, context=context)
            partner = user.company_id.partner_id        
            inter_ask = []
            
            for line in lines:
                if line.motif == u'supply':
                    site_infos = ''
                    description = u'Une livraison est nécessaire pour la réservation %s sur le site %s du %s au %s, il faut livrer les ressources suivantes : \n' % (resa.name, resa.site_id and resa.site_id.name or 'inconnu', checkin_str, checkout_str)
                    for x in resa.reservation_line:
                        #computes site_infos according to each line and infos_supp field
                        if x.infos:
                            site_infos += _(x.reserve_product.name_template + ' : ' + x.infos + '\n')
                        #computes description field content
                        description += str(x.qte_reserves) + ' ' + x.reserve_product.name_template + '\n'

                    service_id = line.service_id.id
                    values = {'name':'Livraison pour la Réservation : ' + resa.name, 
                              'site_details':site_infos,
                              'description':description,
                              'partner_id':partner.id, 
                              'partner_address':partner.address[0].id,
                              'partner_type':partner.type_id and partner.type_id.id or False,
                              'partner_type_code':partner.type_id and partner.type_id.code or False,
                              'site1':resa.site_id.id,
                              'service_id':service_id,
                              'state':'wait',
                              }
                    inter_ask.append(self.pool.get("openstc.ask").create(cr, uid, values, context=context))
                else:
                    #Générer intervention(s) selon le champs "service_id" du produit
                    service_id = line.service_id.id
                    values = {'name':'Mise en place de %s %s sur le site %s' % (str(line.qte_reserves) ,line.product_id.name_template, resa.site_id and resa.site_id.name or 'inconnu'), 
                              'site_details':line.site_details,
                              'description':'Mise en place de %s %s sur le site %s dans le cadre de l\'événement "%s" car l\'installation de cette ressource sur site nécessite une manipulation technique' %(str(line.qte_reserves) ,line.product_id.name_template , resa.name,resa.site_id and resa.site_id.name or 'inconnu'),
                              'partner_id':partner.id, 
                              'partner_address':partner.address[0].id,
                              'partner_type':partner.type_id and partner.type_id.id or False,
                              'partner_type_code':partner.type_id and partner.type_id.code or False,
                              'site1':resa.site_id.id,
                              'service_id':service_id,
                              'state':'wait',
                              }
                    inter_ask.append(self.pool.get("openstc.ask").create(cr, uid, values, context=context))
                
            if len(inter_ask) == len(lines):
                wf_service = netsvc.LocalService('workflow')
                wf_service.trg_validate(uid, 'hotel.reservation', resa.id, 'put_in_use', cr)
            else:
                #print for debug
                print(values)
                raise osv.except_osv('Erreur','Une erreur est survenue lors de la génération des interventions')
        return {'type':'ir.actions.act_window_close'}
    
    def put_in_use_without_intervention(self, cr, uid, ids,context=None):
        if 'active_id' in context:
            resa = self.pool.get("hotel.reservation").browse(cr, uid, context['active_id'])
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'hotel.reservation', resa.id, 'put_in_use', cr)
        return {'type':'ir.actions.act_window_close'}
    
openstc_pret_deliver_products_wizard()

class openstc_pret_deliver_products_line_wizard(osv.osv_memory):
    _name = 'openstc.pret.deliver.products.line.wizard'
    
    _AVAILABLE_MOTIF_VALUES = [('supply','Livraison'),('technical','Installation Technique')]
    
    _columns = {
        'wizard_id':fields.many2one('openstc.pret.deliver.products.wizard', 'Wizard parent'),
        'service_id':fields.many2one('openstc.service','Service Concerné'),
        'motif':fields.selection(_AVAILABLE_MOTIF_VALUES, 'Motif de l\'Intervention',size=128),
        'to_generate':fields.boolean('A Générer ?'),
        'product_id':fields.many2one('product.product', 'Ressource concernée'),
        'site_details':fields.char('Détails du Site',size=128),
        'qte_reserves':fields.integer('Quantité de la Ressource'),
        }
    
    _defaults = {
        'to_generate':lambda *a: 1,
        }
openstc_pret_deliver_products_line_wizard()
    
    
