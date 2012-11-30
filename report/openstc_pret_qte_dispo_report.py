# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import fields,osv
from calendar import monthrange
from datetime import datetime
import tools

class openstock_qte_dispo_report(osv.osv):
    """
    objet pour statistiques
    Chaque enregistrement correspond à une journée dans le mois actuel, dans chaque journée on indique le nombre
    de produits restants (dispo en reservation)
    """
    def _calc_qte_dispo(self, cr, uid, ids, name, args, context=None):
        print("Début fonction calcul champs")
        
        """
        Attribue pour chaque jour du mois la qté de produits réservés (résa en draft (en option ou non) ou confirm seulement)
        """
        #renvoi (1st_weekday_of_mounth, nb_days)
        aujourdhui = datetime.now()
        max = monthrange(aujourdhui.year, aujourdhui.month)
        day = 1
        debut_base = aujourdhui.replace(day=1, hour=0, minute=0, second=0)
        fin_base = aujourdhui.replace(day=max[1], hour=23, minute=59, second=59)
        mois_base = aujourdhui.month
        print(debut_base)
        print(fin_base)
        print(context)
        if 'product_ids' in context:
            prod = context['product_ids']
        else:
            prod = []
        
        if prod <> []:
            """line_ids = self.pool.get("hotel_reservation_line").search(cr, uid, [('reserve_product', 'in', prod)])
            self.pool.get("hotel_reservation").search(cr, uid, ['|',('checkin', '>=', debut_base), ('checkout', '<=', fin_base), ('id', 'in', line_ids)])
            """
            #Liste contenant les 31 ids de l'objet actuel, correspondant aux 31 jours du mois
            #exemple : self_ids[3] renvoie l'id de l'objet actuel concernant le 4ème jour du mois
            self_ids = self.search(cr, uid, [])
            
            
            cr.execute("""select hr.id, extract(day from checkin) as jour_debut, extract(day from checkout - checkin) as duree, extract(month from checkin) as debut_mois, extract(month from checkin) as fin_mois, hrl.reserve_product, hrl.qte_reserves
            from hotel_reservation as hr,
            hotel_reservation_line as hrl
            where hr.id = hrl.line_id
            and (hr.checkin, hr.checkout) overlaps (timestamp %s,timestamp %s)
            and hrl.reserve_product in (select product_id from hotel_room where id in %s)
            and hr.state in ('draft','confirm')
            order by hr.checkin, hr.checkout""", (debut_base, fin_base, tuple(prod)))
            #On récupère toutes les résa dont le produit est réservé ce mois-ci
            
            results = cr.fetchall()
            prod_id = results[0][5]
            stock_prod = self.pool.get("product.product")._product_available(cr, uid, [prod_id], ['qty_available'])
            qte_max = stock_prod[prod_id]['qty_available']
            ret = {}.fromkeys(self_ids, qte_max)
            print(ret)
            for data in results:
                #cle contient l'id de la ligne concernée par le jour actuel
                cle = self_ids[int(data[1]) - 1]
                print("cle=" + str(cle))
                fin = int(data[2]) + cle + 1
                print("fin=" + str(fin))
                i = 0
                #Si la résa commence un autre mois
                if data[3] < mois_base:
                    cle = 0
                #Si la résa se finit un autre mois
                if data[4] > mois_base:
                    fin = max[1]
                iteration = range(cle, fin)
                print(iteration)
                for i in iteration:
                    print("iteration:" + str(i))
                    ret[i] -= data[6]
        print ret
        return ret
    
    _name = "openstock.qte.dispo.report"
    _auto = True
    _description = "Disponibilités des Produits"
    #_rec_name = 'openstock_dispo_prod'
    
    _columns={
              'name':fields.char("Description", size=64),
              'qte_dispo':fields.function(_calc_qte_dispo, string="Quantité Disponible", type="integer", readonly=True),
              'jour_dispo':fields.integer("Journée"),
              'prod_dispo':fields.many2one("product.product", "Produit")
        }
    
    _order = 'jour_dispo'
    
                
    
    def init(self, cr):
        """
            CRM Lead Report
            @param cr: the current row, from the database cursor
        """
        
        #Si première utilisation du graphe, on initialise avec les 31 jours max possibles par mois 
        cr.execute("select count(*) from openstock_qte_dispo_report")
        if cr.fetchone()[0] == 0:
            cr.execute("""insert into openstock_qte_dispo_report(jour_dispo) values (1),(2),(3),(4),(5),(6),(7),(8),
            (9),(10),(11),(12),(13),(14),(15),(16),(17),(18),(19),(20),(21),(22),(23),(24),(25),(26),(27),(28),(29),(30),(31) """)
openstock_qte_dispo_report()


class openstock_qte_dispo_reserve_report(osv.osv):
    """ CRM Lead Analysis """
    _name = "openstock.qte.dispo.reserve.report"
    _auto = False
    _description = "Réservation des produits"
    _rec_name = 'produits_reserves'

    _columns = {
        'reservation_no':fields.char("Numéro", size=16),
        'checkin':fields.datetime("Début réservation"),
        'checkout':fields.datetime("Début réservation"),
        'product':fields.many2one("product.product","article réservé"),
        'qte':fields.integer("Quantité réservée")
    }
    
    
    
    
    def init(self, cr):

        tools.drop_view_if_exists(cr, 'produits_reserves')
        cr.execute("""
            CREATE OR REPLACE VIEW produits_reserves AS (
                SELECT
                    hr.reservation_no,
                    hr.checkin,
                    hr.checkout,
                    hrl.reserve_product,
                    hrl.qte_reserves
                FROM
                    hotel_reservation as hr,
                    hotel_reservation_line as hrl
                WHERE hr.state in ('draft','confirm')
            )""")

openstock_qte_dispo_reserve_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

    
    