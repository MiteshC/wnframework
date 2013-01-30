wn.provide('wn.utils');

wn.utils = {
	get_file_link: function(filename) {
		return wn.utils.is_url(filename) || (filename.indexOf("images/")!=-1) || (filename.indexOf("files/")!=-1)
			? filename : 'files/' + filename;
	},
	is_url: function(txt) {
		return txt.toLowerCase().substr(0,7)=='http://'
			|| txt.toLowerCase().substr(0,8)=='https://'
	},
	filter_dict: function(dict, filters) {
		var ret = [];
		if(typeof filters=='string') {
			return [dict[filters]]
		}
		$.each(dict, function(i, d) {
			for(key in filters) {
				if($.isArray(filters[key])) {
					if(filters[key][0]=="in") {
						if(filters[key][1].indexOf(d[key])==-1)
							return;
					} else if(filters[key][0]=="not in") {
						if(filters[key][1].indexOf(d[key])!=-1)
							return;
					}
				} else {
					if(d[key]!=filters[key]) return;
				}
			}
			ret.push(d);
		});
		return ret;
	},
	comma_or: function(list) {
		return wn.utils.comma_sep(list, " " + wn._("or") + " ");
	},
	comma_and: function(list) {
		return wn.utils.comma_sep(list, " " + wn._("and") + " ");
	},
	comma_sep: function(list, sep) {
		if(list instanceof Array) {
			if(list.length==0) {
				return "";
			} else if (list.length==1) {
				return list[0];
			} else {
				return list.slice(0, list.length-1).join(", ") + sep + list.slice(-1)[0];
			}
		} else {
			return list;
		}
	},
	set_intro: function(me, wrapper, txt) {
		if(!me.intro_area) {
			me.intro_area = $('<div class="alert form-intro-area" style="margin-top: 20px;">')
				.prependTo(wrapper);
		}
		if(txt) {
			if(txt.search(/<p>/)==-1) txt = '<p>' + txt + '</p>';
			me.intro_area.html(txt);
		} else {
			me.intro_area.remove();
			me.intro_area = null;
		}
	},
	set_footnote: function(me, wrapper, txt) {
		if(!me.footnote_area) {
			me.footnote_area = $('<div class="alert form-intro-area" style="margin-top: 20px;">')
				.insertAfter(wrapper.lastChild);
		}
		
		if(txt) {
			if(txt.search(/<p>/)==-1) txt = '<p>' + txt + '</p>';
			me.footnote_area.html(txt);
		} else {
			me.footnote_area.remove();
			me.footnote_area = null;
		}
	},
	get_args_dict_from_url: function(txt) {
		var args = {};
		$.each(decodeURIComponent(txt).split("&"), function(i, arg) {
			arg = arg.split("=");
			args[arg[0]] = arg[1]
		});
		return args;
	},
	get_url_from_dict: function(args) {
		return encodeURIComponent($.map(args, function(val, key)	{ return key+"="+val; }).join("&") || "");
	},
	disable_export_btn: function(btn) {
		if(!wn.user.is_report_manager()) {
			btn.attr("disabled", "disabled").attr("title", 
				wn._("Can only be exported by users with role 'Report Manager'"));
		}		
	},
	validate_type: function ( val, type ) {
		// from https://github.com/guillaumepotier/Parsley.js/blob/master/parsley.js#L81
		var regExp;

		switch ( type ) {
			case "number":
				regExp = /^-?(?:\d+|\d{1,3}(?:,\d{3})+)?(?:\.\d+)?$/;
				break;
			case "digits":
				regExp = /^\d+$/;
				break;
			case "alphanum":
				regExp = /^\w+$/;
				break;
			case "email":
				regExp = /^((([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+(\.([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+)*)|((\x22)((((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(([\x01-\x08\x0b\x0c\x0e-\x1f\x7f]|\x21|[\x23-\x5b]|[\x5d-\x7e]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(\\([\x01-\x09\x0b\x0c\x0d-\x7f]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]))))*(((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(\x22)))@((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))$/i;
				break;
			case "url":
				regExp = /^(https?|s?ftp):\/\/(((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:)*@)?(((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5]))|((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.?)(:\d*)?)(\/((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)+(\/(([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)*)*)?)?(\?((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|[\uE000-\uF8FF]|\/|\?)*)?(#((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|\/|\?)*)?$/i;
				break;
			case "dateIso":
				regExp = /^(\d{4})\D?(0[1-9]|1[0-2])\D?([12]\d|0[1-9]|3[01])$/;
				break;
			default:
				return false;
				break;
		}

		// test regExp if not null
		return '' !== val ? regExp.test( val ) : false;
	}
};