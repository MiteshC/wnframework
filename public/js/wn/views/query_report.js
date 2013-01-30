// Copyright 2013 Web Notes Technologies Pvt Ltd
// License: MIT. See license.txt

wn.provide("wn.views");

wn.views.QueryReport = Class.extend({
	init: function(opts) {
		$.extend(this, opts);
		// globalify for slickgrid
		this.appframe = this.parent.appframe;
		this.parent.query_report = this;
		this.make();
	},
	slickgrid_options: {
		enableColumnReorder: false,
	    showHeaderRow: true,
	    headerRowHeight: 30,
	    explicitInitialization: true,
	    multiColumnSort: true		
	},	
	make: function() {
		this.wrapper = $("<div>").appendTo($(this.parent).find(".layout-main"));
		$('<div class="query-edit well" style="display: none;">\
			<div class="query-form" style="width: 60%; float: left;"></div>\
			<div class="help" style="width: 30%; float: left; margin-left: 15px;">\
				<b>Column Rules: "label:datatype:width"</b><br>\
				<ol>\
					<li>"datatype" and "width" are optional.\
					<li>"datatype" can be "Link", "Date", "Float", "Currency".\
					<li>'+wn._('For Links, use define linked')+' DocType as "Link/Customer".<br>\
					Example: "Customer:Link/Customer:120"\
				</ol>\
			</div>\
			<div class="clear"></div>\
		</div>\
		<div class="waiting-area" style="display: none;"></div>\
		<div class="no-report-area well" style="display: none;">\
		</div>\
		<div class="results" style="display: none;">\
			<div class="result-area" style="height:400px; \
				border: 1px solid #aaa;"></div>\
			<p class="help"><br>\
				'+wn._('For comparative filters, start with')+' ">" or "<", e.g. >5 or >01-02-2012\
				<br>'+wn._('For ranges')+' ('+wn._('values and dates')+') use ":", \
					e.g. "5:10" (to filter values between 5 & 10)</p>\
		</div>').appendTo(this.wrapper);

		this.make_query_form();
		this.make_toolbar();
	},
	make_toolbar: function() {
		var me = this;
		this.appframe.add_button(wn._("Run"), function() {
			me.refresh();
		}).addClass("btn-success");
		
		// Edit
		var edit_btn = this.appframe.add_button(wn._("Edit"), function() {
			me.wrapper.find(".query-edit").slideToggle();
		});
		if(!in_list(user_roles, "System Manager")) {
			edit_btn.attr("disabled", "disabled")
				.attr("title", wn._("Only System Manager can create / edit reports"));
		}

		var export_btn = this.appframe.add_button(wn._("Export"), function() {
			me.export();
		});
		wn.utils.disable_export_btn(export_btn);
	},
	make_query_form: function() {
		this.query_form = new wn.ui.FieldGroup({
			parent: $(this.wrapper).find(".query-form").get(0),
			fields: [
				{label:wn._("Report Name"), reqd: 1, fieldname:"name"},
				{label:wn._("Based on"), fieldtype:"Link", options:"DocType",
					fieldname: "ref_doctype",
					reqd:1, description:wn._("Permissions will be based on this DocType")},
				{label:wn._("Query"), fieldtype: "Text", reqd: 1, fieldname:"query"},
				{label:wn._("Save"), fieldtype:"Button", fielname:"save"}
			]
		});
		
		// text style
		$(this.query_form.fields_dict.query.input).css({
			width: "100%", 
			height: "300px",
			"font-weight": "Normal", 
			"font-family": "Monaco, Courier, Fixed",
		});
		
		// Save
		var me = this;
		$(this.query_form.fields_dict.save.input).click(function() {
			var doc = me.query_form.get_values();
			if(!doc) return;
	
			// new report
			if(!me.doc || (me.doc.name != doc.name)) {
				doc.doctype = "Report";
				doc.__islocal = 1;
				if(user=="Administrator") 
					doc.is_standard="Yes";
				else 
					doc.is_standard="No"
			} else{
				doc = $.extend(copy_dict(me.doc), doc);
			}
			
			wn.call({
				method:"webnotes.client.save",
				args: { doclist: [doc] },
				callback: function(r) {
					if(!r.exc) {
						msgprint(wn._("Report Saved"))
					}
					wn.provide("locals.Report");
					me.doc = r.message[0]
					locals["Report"][me.doc.name] = r.message[0];
					wn.set_route("query-report", me.doc.name);
				}
			})
		});
	},
	load: function() {
		// load from route
		var route = wn.get_route();
		var me = this;
		this.doc = null;
		if(route[1]) {
			this.wrapper.find(".no-report-area").toggle(false);
			wn.model.with_doc("Report", route[1], function(docname) {
				me.doc = locals["Report"] && locals["Report"][route[1]];
				if(!me.doc) {
					msgprint(wn._("Not allowed"));
					return;
				}
				me.appframe.title(wn._("Query Report")+": " + me.doc.name);
				me.query_form.set_values(me.doc);

				// only administrator can edit standard reports
				$(me.wrapper).find("query-form :input").attr('disabled',
					(me.doc.is_standard=="Yes" && user!="Administrator")
					? "disabled" : null);
				me.refresh();
			})
		} else {
			var msg = "No Report Loaded. "
			if(in_list(user_roles, "System Manager"))
				msg += wn._("Click on edit button to start a new report.");
			else
				msg += wn._("Please click on another report from the menu.");
			this.wrapper.find(".no-report-area").html(msg).toggle(true);	
		}
	},
	refresh: function() {
		// Run
		var me =this;
		this.waiting = wn.messages.waiting(this.wrapper.find(".waiting-area").toggle(true), 
			"Loading Report...");
		wn.call({
			method: "webnotes.widgets.query_report.run",
			args: {
				doctype: me.ref_doctype || me.query_form.get_value("ref_doctype"),
				query: me.query || me.query_form.get_value("query")
			},
			callback: function(r) {
				me.make_results(r.message.result, r.message.columns);
			}
		})		
	},
	make_results: function(result, columns) {
		this.wrapper.find(".waiting-area").empty().toggle(false);
		this.wrapper.find(".results").toggle(true);
		this.make_columns(columns);
		this.make_data(result, columns);
		this.render(result, columns);
	},
	render: function(result, columns) {
		this.columnFilters = {};
		this.make_dataview();
		this.id = wn.dom.set_unique_id($(this.wrapper.find(".result-area")).get(0));
		
		this.grid = new Slick.Grid("#"+this.id, this.dataView, this.columns, 
			this.slickgrid_options);
		this.setup_header_row();
		this.grid.init();
		this.setup_sort();
	},
	make_columns: function(columns) {
		this.columns = [{id: "_id", field: "_id", name: "Sr No", width: 60}]
			.concat($.map(columns, function(c) { 
				var col = {name:c, id: c, field: c, sortable: true, width: 80}					

				if(c.indexOf(":")!=-1) {
					var opts = c.split(":");

					// link
					if(opts[1].substr(0,4)=="Link") {
						col.doctype = opts[1].split('/')[1];
						col.formatter = function(row, cell, value, columnDef, dataContext) {
							return repl('<a href="#Form/%(doctype)s/%(name)s">%(name)s</a>', {
								doctype: columnDef.doctype,
								name: value
							});
						}
					} else if(opts[1]=="Date") {
						col.formatter = function(row, cell, value, columnDef, dataContext) {
							return dateutil.str_to_user(value);
						};
					} else if(opts[1]=="Currency") {
						col.formatter = function(row, cell, value, columnDef, dataContext) {
							return repl('<div style="text-align: right;">%(value)s</div>', {
								value: format_number(value)
							});
						};
					} else if(opts[1]=="Float") {
						col.formatter = function(row, cell, value, columnDef, dataContext) {
							return repl('<div style="text-align: right;">%(value)s</div>', {
								value: flt(value).toFixed(6)
							});
						};
					} else if(opts[1]=="Int") {
						col.formatter = function(row, cell, value, columnDef, dataContext) {
							return repl('<div style="text-align: right;">%(value)s</div>', {
								value: parseInt(value)
							});
						};
					}
					
					col.name = col.id = col.field = opts[0];
					col.fieldtype = opts[1];

					// width
					if(opts[2]) {
						col.width=parseInt(opts[2]);
					}		
				}
				col.name = toTitle(col.name.replace(/ /g, " "))
				return col
		}));
	},
	make_data: function(result, columns) {
		var me = this;
		this.data = $.map(result, function(row, row_idx) {
			var newrow = {};
			for(var i=1, j=me.columns.length; i<j; i++) {
				newrow[me.columns[i].field] = row[i-1];
			};
			newrow._id = row_idx + 1;
			newrow.id = newrow.name ? newrow.name : ("_" + newrow._id);
			return newrow;
		});
	},
	make_dataview: function() {
		// initialize the model
		this.dataView = new Slick.Data.DataView({ inlineFilters: true });
		this.dataView.beginUpdate();
		this.dataView.setItems(this.data);
		this.dataView.setFilter(this.inline_filter);
		this.dataView.endUpdate();
		
		var me = this;
		this.dataView.onRowCountChanged.subscribe(function (e, args) {
			me.grid.updateRowCount();
			me.grid.render();
		});

		this.dataView.onRowsChanged.subscribe(function (e, args) {
			me.grid.invalidateRows(args.rows);
			me.grid.render();
		});
	},
	inline_filter: function (item) {
		var me = wn.container.page.query_report;
		for (var columnId in me.columnFilters) {
			if (columnId !== undefined && me.columnFilters[columnId] !== "") {
				var c = me.grid.getColumns()[me.grid.getColumnIndex(columnId)];
				if (!me.compare_values(item[c.field], me.columnFilters[columnId], 
						me.columns[me.grid.getColumnIndex(columnId)])) {
					return false;
				}
			}
		}
		return true;
	},
	compare_values: function(value, filter, columnDef) {
		var invert = false;
		
		// check if invert
		if(filter[0]=="!") {
			invert = true;
			filter = filter.substr(1);
		}
		
		var out = false;
		var cond = "=="
		
		// parse condition
		if(filter[0]==">") {
			filter = filter.substr(1);
			cond = ">"
		} else if(filter[0]=="<") {
			filter = filter.substr(1);
			cond = "<"
		} 
		
		
		if(in_list(['Float', 'Currency', 'Int', 'Date'], columnDef.fieldtype)) {
			// non strings
			if(filter.indexOf(":")==-1) {
				if(columnDef.fieldtype=="Date") {
					filter = dateutil.user_to_str(filter);
				}

				if(in_list(["Float", "Currency", "Int"], columnDef.fieldtype)) {
					value = flt(value);
					filter = flt(filter);
				}

				out = eval("value" + cond + "filter");
			} else {
				// range
				filter = filter.split(":");
				if(columnDef.fieldtype=="Date") {
					filter[0] = dateutil.user_to_str(filter[0]);
					filter[1] = dateutil.user_to_str(filter[1]);
				}

				if(in_list(["Float", "Currency", "Int"], columnDef.fieldtype)) {
					value = flt(value);
					filter[0] = flt(filter[0]);
					filter[1] = flt(filter[1]);
				}
				
				out = value >= filter[0] && value <= filter[1];
			}
		} else {
			// string
			value = value + "";
			value = value.toLowerCase();
			filter = filter.toLowerCase();
			out = value.indexOf(filter) != -1;
		}
		
		if(invert) 
			return !out;
		else 
			return out;
	},
	setup_header_row: function() {
		var me = this;
		
		$(this.grid.getHeaderRow()).delegate(":input", "change keyup", function (e) {
			var columnId = $(this).data("columnId");
			if (columnId != null) {
				me.columnFilters[columnId] = $.trim($(this).val());
				me.dataView.refresh();
			}
		});

		this.grid.onHeaderRowCellRendered.subscribe(function(e, args) {
			$(args.node).empty();
			$("<input type='text'>")
				.data("columnId", args.column.id)
				.val(me.columnFilters[args.column.id])
				.appendTo(args.node);
		});
	},
	setup_sort: function() {
		var me = this;
		this.grid.onSort.subscribe(function (e, args) {
			var cols = args.sortCols;

			me.data.sort(function (dataRow1, dataRow2) {
				for (var i = 0, l = cols.length; i < l; i++) {
					var field = cols[i].sortCol.field;
					var sign = cols[i].sortAsc ? 1 : -1;
					var value1 = dataRow1[field], value2 = dataRow2[field];
					var result = (value1 == value2 ? 0 : (value1 > value2 ? 1 : -1)) * sign;
					if (result != 0) {
						return result;
					}
				}
				return 0;
			});
			me.dataView.beginUpdate();
			me.dataView.setItems(me.data);
			me.dataView.endUpdate();
			me.dataView.refresh();
	    });
	},
	export: function() {
		var result = $.map(wn.slickgrid_tools.get_view_data(this.columns, this.dataView),
		 	function(row) {
				return [row.splice(1)];
		});
		this.title = this.query_form.get_value("name");
		wn.tools.downloadify(result, ["Report Manager", "System Manager"], this);
		return false;
	}
})