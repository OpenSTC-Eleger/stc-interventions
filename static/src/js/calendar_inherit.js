/*
 * OpenSTC Interventions - Openerp Module to manage Cityhall technical department
 * Copyright (C) 2013 Siclic www.siclic.fr
 *
 * This file is part of OpenSTC Interventions.
 *
 * OpenSTC Interventions is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * OpenSTC Interventions is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with OpenSTC Interventions.  If not, see <http://www.gnu.org/licenses/>.
 */

openerp.openstc = function(openerp) {
	t = openerp.web._t,
    _lt = openerp.web._lt;
	var openstc_init_dates = new Date();
	openerp.web_calendar.CalendarView = openerp.web_calendar.CalendarView.extend({
	    init: function(parent, dataset, view_id, options) {
	    	this._super(parent, dataset, view_id, options)
	    	//if user pass start_calendar in it's action descriptor context, we use it to start calendar at this date
	    	if(options.action && options.action.context){
	    		if(options.action.context.start_calendar){
	    			openstc_init_dates = new Date(options.action.context.start_calendar.split(' ').join('T'));
	    		}
	    	}
	    },
		init_scheduler: function(){
			this._super();
			this.update_range_dates(openstc_init_dates);
			scheduler.setCurrentView(openstc_init_dates,this.mode || 'week');
		}
	});
	
};