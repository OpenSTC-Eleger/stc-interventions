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
from osv import fields, osv
import netsvc
import time
import base64
import re
from datetime import datetime,timedelta
from datetime import datetime
from mx.DateTime.mxDateTime import strptime
from openbase.openbase_core import OpenbaseCore


class ask(OpenbaseCore):
    _inherit = "openstc.ask"

    """
    @param record: browse_record of hotel.reservation for which to generate hotel.folio report
    @return: id or attachment created for this record
    @note: hotel.folio report is created on hotel.reservation because hotel.folio has not any form view for now
    """

    def envoyer_mail(self, cr, uid, ids, vals=None, attach_ids=[], context=None):
        #TODO: check if company wants to send email (info not(opt_out) in partner)
        #We keep only resa where partner have not opt_out checked
        resa_ids_notif = []
        inter = self.browse(cr, uid, ids[0])
        if not inter.partner_id.opt_out :
            email_obj = self.pool.get("email.template")
            email_tmpl_id = 0
            prod_attaches = {}
            data_obj = self.pool.get('ir.model.data')
            model_map = { 'valid':'openstc_email_template_ask_valid',
                         'finished':'openstc_email_template_ask_finished'}
            #first, retrieve template_id according to 'state' parameter
            if vals.get('state','') in model_map.keys():
                email_tmpl_id = data_obj.get_object_reference(cr, uid, 'openstc',model_map.get(vals.get('state')))[1]
                #special behavior for confirm notifications
                if vals['state'] == 'validated':
                    #Search for product attaches to be added to email
                    prod_ids = []
                    for resa in self.browse(cr, uid, ids):
                        prod_ids.extend([line.reserve_product.id for line in resa.reservation_line])
                    if prod_ids:
                        cr.execute("select id, res_id from ir_attachment where res_id in %s and res_model=%s order by res_id", (tuple(prod_ids), 'product.product'))
                        #format sql return to concat attaches with each prod_id
                        for item in cr.fetchall():
                            prod_attaches.setdefault(item[1],[])
                            prod_attaches[item[1]].append(item[0])

                if email_tmpl_id:
                    if isinstance(email_tmpl_id, list):
                        email_tmpl_id = email_tmpl_id[0]
                    #generate mail and send it with optional attaches
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

        return True

openstc_ask()