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
#    the Free Software Foundation, either version 3 of the License, ors_user
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

from osv import osv, fields

#----------------------------------------------------------
# Equipments
#----------------------------------------------------------

class equipment(osv.osv):
    _name = "openstc.equipment"
    _description = "openstc.equipment"
    #_inherit = 'product.product'
    _inherits = {'product.product': "product_product_id"}

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','type'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['type']:
                name =  name + ' / '+ record['type']
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _columns = {
            'immat': fields.char('Imatt', size=128),
            'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
            'product_product_id': fields.many2one('product.product', 'Product', help="", ondelete="cascade"),
            #Service authorized for use equipment
            'service_ids':fields.many2many('openstc.service', 'openstc_equipment_services_rel', 'equipment_id', 'service_id', 'Services'),
            #Service owner
            'service':fields.many2one('openstc.service', 'Service'),

            'marque': fields.char('Marque', size=128),
            'type': fields.char('Type', size=128),
            'usage': fields.char('Usage', size=128),

            'technical_vehicle': fields.boolean('Technical vehicle'),
            'commercial_vehicle': fields.boolean('Commercial vehicle'),

            'small_material': fields.boolean('Small'),
            'fat_material': fields.boolean('Fat'),

            'cv': fields.integer('CV', select=1),
            'year': fields.integer('Year', select=1),
            'time': fields.integer('Time', select=1),
            'km': fields.integer('Km', select=1),



            #Calcul total price and liters
            #'oil_qtity': fields.integer('oil quantity', select=1),
            #'oil_price': fields.integer('oil price', select=1),
    }


equipment()


#----------------------------------------------------------
# Services
#----------------------------------------------------------

class service(osv.osv):
    _name = "openstc.service"
    _description = "openstc.service"
    _rec_name = "name"

    _columns = {
            'name': fields.char('Name', size=128, required=True),
            'favcolor':  fields.char('Name', size=128),
            'code': fields.char('Code', size=32, required=True),
            'service_id':fields.many2one('openstc.service', 'Service Parent'),
            'technical': fields.boolean('Technical service'),
            'manager_id': fields.many2one('res.users', 'Manager'),
            'user_ids': fields.one2many('res.users', 'service_id', "Users"),
    }
service()


#----------------------------------------------------------
# Sites
#----------------------------------------------------------

class site_type(osv.osv):
    _name = "openstc.site.type"
    _description = "openstc.site.type"

    _columns = {
            'name': fields.char('Name', size=128, required=True),
            'code': fields.char('Code', size=32, required=True),
    }
site_type()

class site(osv.osv):
    _name = "openstc.site"
    _description = "openstc.site"

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','type'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['type']:
                name =  name + ' / '+ record['type'][1]
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _columns = {

            'name': fields.char('Name', size=128, required=True),
            'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
            'code': fields.char('Code', size=32),
            'type': fields.many2one('openstc.site.type', 'Type', required=True),
            'service_ids':fields.many2many('openstc.service', 'openstc_site_services_rel', 'site_id', 'service_id', 'Services'),
            #'service': fields.many2one('openstc.service', 'Service', required=True),
            'site_parent_id': fields.many2one('openstc.site', 'Site parent', help='Site parent', ondelete='set null'),
            'lenght': fields.integer('Lenght'),
            'width': fields.integer('Width'),
            'surface': fields.integer('Surface'),
            'long': fields.float('Longitude'),
            'lat': fields.float('Latitude'),
    }

#    def search_count(self, cr, user, args, context=None):
#        time.sleep(50)
#        return super(site, self).search_count(cr, user, args, context)

site()

#----------------------------------------------------------
# Partner
#----------------------------------------------------------

class openstc_partner_type(osv.osv):
    _name = "openstc.partner.type"
    _description = "openstc.partner.type"
    _rec_name = "name"

    _columns = {
            'name': fields.char('Name', size=128, required=True),
            'code': fields.char('Code', size=32, required=True),
            'claimers': fields.one2many('res.partner', 'type_id', "Claimers"),
    }
openstc_partner_type()
 
class res_partner(osv.osv):
     _inherit = "res.partner"

     _columns = {
         'type_id': fields.many2one('openstc.partner.type', 'Type'),
 
 }
res_partner()
 
class groups(osv.osv):
    _name = "res.groups"
    _description = "Access Groups"
    _inherit = "res.groups"
    _rec_name = 'full_name'

    _columns = {
        'code': fields.char('Code', size=128),
        'perm_request_confirm' : fields.boolean('Demander la Confirmation'),
    }

groups()

class users(osv.osv):
    _name = "res.users"
    _description = "res users st"
    _inherit = "res.users"
    _rec_name = "name"

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','firstname'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['firstname']:
                name =  record['firstname'] + '  '+  name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    #Calculates if agent belongs to 'arg' code group
    def _get_group(self, cr, uid, ids, fields, arg, context):
         res = {}
         user_obj = self.pool.get('res.users')
         group_obj = self.pool.get('res.groups')

         for id in ids:
            user = user_obj.read(cr, uid, id,['groups_id'],context)
            #Get 'arg' group (MANAGER or DIRECTOR)
            group_ids = group_obj.search(cr, uid, [('code','=', arg),('id','in',user['groups_id'])])
            res[id] = True if len( group_ids ) != 0 else False
         return res




    _columns = {
            'firstname': fields.char('firstname', size=128),
            'lastname': fields.char('lastname', size=128),
            'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
            'service_id':fields.many2one('openstc.service', 'Service    '),
            'service_ids': fields.many2many('openstc.service', 'openstc_user_services_rel', 'user_id', 'service_id', 'Services'),
            'cost': fields.integer('Coût horaire'),
            'post': fields.char('Post', size=128),
            'position': fields.char('Grade', size=128),
            'arrival_date': fields.datetime('Date d\'arrivée'),
            'birth_date': fields.datetime('Date de naissance'),
            'address_home': fields.char('Address', size=128),
            'city_home': fields.char('City', size=128),
            'phone': fields.char('Phone Number', size=12),

            'team_ids': fields.many2many('openstc.team', 'openstc_team_users_rel', 'user_id', 'team_id', 'Teams'),
            'manage_teams': fields.one2many('openstc.team', 'manager_id', "Teams"),
            'isDST' : fields.function(_get_group, arg="DIRE", method=True,type='boolean', store=False), #DIRECTOR group
            'isManager' : fields.function(_get_group, arg="MANA", method=True,type='boolean', store=False), #MANAGER group

    }

    def create(self, cr, uid, data, context={}):
        #_logger.debug('create USER-----------------------------------------------');
        res = super(users, self).create(cr, uid, data, context)

        company_ids = self.pool.get('res.company').name_search(cr, uid, name='STC')
        if len(company_ids) == 1:
            data['company_id'] = company_ids[0][0]
        else:
            data['company_id'] = 1;
        if data.has_key('isManager')!=False and data['isManager']==True :
            self.set_manager(cr, uid, [res], data, context)
        #TODO
        #else

        return res

    def write(self, cr, uid, ids, data, context=None):

        if data.has_key('isManager')!=False and data['isManager']==True :
            self.set_manager(cr, uid, ids, data, context)

        res = super(users, self).write(cr, uid, ids, data, context=context)
        return res

    def set_manager(self, cr, uid, ids, data,context):

        service_obj = self.pool.get('openstc.service')

        group_obj = self.pool.get('res.groups')
        #Get officer group (code group=OFFI)
        group_id = group_obj.search(cr, uid, [('code','=','OFFI')])[0]

        service_id = service_obj.browse(cr, uid, data['service_id'], context=context)
        #Previous manager become an agent
        manager = service_obj.read(cr, uid, data['service_id'],
                                    ['manager_id'], context)
        if manager and manager['manager_id']:
            self.write(cr, uid, [manager['manager_id'][0]], {
                    'groups_id' : [(6, 0, [group_id])],
                }, context=context)

        #Update service : current user is service's manager
        service_obj.write(cr, uid, data['service_id'], {
                 'manager_id': ids[0],
             }, context=context)

            #Calculates the agents can be added to the team


    #Get lists officers/teams where user is the referent on
    def getTeamsAndOfficers(self, cr, uid, ids, data, context=None):
        res = {}
        user_obj = self.pool.get('res.users')
        team_obj = self.pool.get('openstc.team')


        #get list of all agents
        all_officer_ids = user_obj.search(cr, uid, []);
        all_team_ids = team_obj.search(cr, uid, []);

        #get list of all teams
        all_officers = user_obj.browse(cr, uid, all_officer_ids, context);
        all_teams = team_obj.browse(cr, uid, all_team_ids, context);

        officers = []
        teams = []
        managerTeamID = []

        res['officers'] = []
        res['teams'] = []
        newOfficer = {}
        newTeam = {}
        #get user
        user = self.browse(cr, uid, uid, context=context)
        #If users connected is the DST get all teams and all officers
        if user.isDST:
            #Serialize each officer with name and firstname
            for officer in user_obj.read(cr, uid, all_officer_ids, ['id','name','firstname']):
                newOfficer = { 'id'  : officer['id'],
                               'name' : officer['name'],
                               'firstname' : officer['firstname']
                            }
                officers.append(newOfficer)
            res['officers'] =  officers

            #Serialize each team with name, manager and officers (with name and firstname)
            for team in team_obj.read(cr, uid, all_team_ids, ['id','name','manager_id','members']):
                newTeam = { 'id'   : team['id'] ,
                            'name' : team['name'],
                            'manager_id' : team['manager_id'],
                            'members' :  team_obj._get_members(cr, uid, [team['id']],None,None,context)
                            }
                teams.append(newTeam)
            res['teams'] = teams
        #If user connected is Manager get all teams and all officers where he is the referent
        elif user.isManager :
            #For each services authorized for user
            for service_id in user.service_ids :
                #For each officer
                for officer in all_officers:
                    if not officer.isDST :
                        #Check if officer's services list is in user's services list
                        if (service_id in officer.service_ids) and (officer.id not in officers):
                            newOfficer = { 'id'  : officer.id,
                                          'name' : officer.name,
                                          'firstname' : officer.firstname
                                          }
                            officers.append(newOfficer)
                res['officers'] = officers
                for team in all_teams:
                    if (service_id in team.service_ids) and (team.id not in teams):
                        manager_id = False
                        if isinstance(team.manager_id, browse_null)!= True :
                            manager_id = team.manager_id.id
                        newTeam = { 'id'   : team.id ,
                            'name' : team.name,
                            'manager_id' : manager_id,
                            'members' : team_obj._get_members(cr, uid, [team.id],None,None,context)
                            }
                        teams.append(newTeam)
                res['teams'] = teams
        #If user connected is an officer
        else:
            #Get all teams where officer is manager on it
            for team_id in user.manage_teams :
                managerTeamID.append(team_id.id)
            if len(managerTeamID) > 0 :
                #For each officer
                for officer in all_officers:
                    if not officer.isDST :
                        #Check if user is the manager on officer's teams
                        for team_id in officer.team_ids :
                            if (team_id.id in managerTeamID) and (officer.id not in officers) :
                                newOfficer = { 'id'  : officer.id,
                                              'name' : officer.name,
                                              'firstname' : officer.firstname
                                          }
                                officers.append(newOfficer)
                                break
                res['officers'] = officers

        return res


users()

class team(osv.osv):
    _name = "openstc.team"
    _description = "team stc"
    _rec_name = "name"


    #Calculates the agents can be added to the team
    def _get_free_users(self, cr, uid, ids, fields, arg, context):
        res = {}
        user_obj = self.pool.get('res.users')
        group_obj = self.pool.get('res.groups')

        for id in ids:
            #get current team object
            team = self.browse(cr, uid, id, context=context)
            team_users = []
            #get list of agents already belongs to team
            for user_record in team.user_ids:
                team_users.append(user_record.id)
            #get list of all agents
            all_users = user_obj.search(cr, uid, []);

            free_users = []
            for user_id in all_users:
                #get current agent object
                user = user_obj.read(cr, uid, user_id,['groups_id'],context)
                #Current agent is DST (DIRECTOR group)?
                group_ids = group_obj.search(cr, uid, [('code','=','DIRE'),('id','in',user['groups_id'])])
                #Agent must not be DST and not manager of team and no already in team
                if (len( group_ids ) == 0) and (user_id != team.manager_id.id) and (user_id not in team_users):
                    free_users.append(user_id)

            res[id] = free_users

        return res


    _columns = {
            'name': fields.char('name', size=128),
            'manager_id': fields.many2one('res.users', 'Manager'),
            'service_ids': fields.many2many('openstc.service', 'openstc_team_services_rel', 'team_id', 'service_id', 'Services'),
            'user_ids': fields.many2many('res.users', 'openstc_team_users_rel', 'team_id', 'user_id', 'Users'),
            'free_user_ids' : fields.function(_get_free_users, method=True,type='many2one', store=False),
    }
    #Calculates the agents can be added to the team
    def _get_members(self, cr, uid, ids, fields, arg, context):
        res = {}
        user_obj = self.pool.get('res.users')
        #for id in ids:
        team = self.browse(cr, uid, ids[0], context=context)
        team_users = []
        #get list of agents already belongs to team
        for user_record in team.user_ids:
             officer = user_obj.read(cr, uid, user_record.id,['id','name','firstname'],context)
             officerSerialized = { 'id'  : officer['id'],
                               'name' : officer['name'],
                               'firstname' : officer['firstname']
                               }
             team_users.append(officerSerialized)
            #res[id] = team_users
        return team_users

team()
 
class product_product(osv.osv):
    _name = "product.product"
    _inherit = "product.product"
    _description = "Produit"

    _columns = {
        'type_prod':fields.selection([('materiel','Matériel'),('fourniture','Fourniture Achetable'),('site','Site')], 'Type de Produit'),
        'openstc_reservable':fields.boolean('Reservable', help='Indicates if this ressource can be reserved or not by tiers'),
        'openstc_maintenance':fields.boolean('Maintenance ?', help='Indicates if this ressource can be associated to contracts for maintenance'),
         }
    _defaults = {
        'openstc_reservable':lambda *a: False,
        'openstc_maintenance':lambda *a: False,
    }
 
product_product()
