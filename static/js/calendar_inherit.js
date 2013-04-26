openerp.openstc_prets = function(openerp) {
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
