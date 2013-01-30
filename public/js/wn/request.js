// Copyright (c) 2012 Web Notes Technologies Pvt Ltd (http://erpnext.com)
// 
// MIT License (MIT)
// 
// Permission is hereby granted, free of charge, to any person obtaining a 
// copy of this software and associated documentation files (the "Software"), 
// to deal in the Software without restriction, including without limitation 
// the rights to use, copy, modify, merge, publish, distribute, sublicense, 
// and/or sell copies of the Software, and to permit persons to whom the 
// Software is furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in 
// all copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
// INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
// PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
// HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
// CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
// OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
//

// My HTTP Request

wn.provide('wn.request');
wn.request.url = 'server.py';

// generic server call (call page, object)
wn.call = function(opts) {
	var args = $.extend({}, opts.args);
	
	// cmd
	if(opts.module && opts.page) {
		args.cmd = opts.module+'.page.'+opts.page+'.'+opts.page+'.'+opts.method;
	} else if(opts.doc) {
		$.extend(args, {
			cmd: "runserverobj",
			docs: wn.model.compress(wn.model.get_doclist(opts.doc.doctype,
				opts.doc.name)),
			method: opts.method,
			args: opts.args,
		});	
	} else if(opts.method) {
		args.cmd = opts.method;
	}
		
	// stringify args if required
	for(key in args) {
		if(args[key] && typeof args[key] != 'string') {
			args[key] = JSON.stringify(args[key]);
		}
	}

	wn.request.call({
		args: args,
		success: opts.callback,
		error: opts.error,
		btn: opts.btn,
		freeze: opts.freeze,
		show_spinner: !opts.no_spinner,
		progress_bar: opts.progress_bar
	});
}


wn.request.call = function(opts) {
	wn.request.prepare(opts);
	var ajax_args = {
		url: opts.url || wn.request.url,
		data: opts.args,
		type: opts.type || 'POST',
		dataType: opts.dataType || 'json',
		success: function(r, xhr) {
			wn.request.cleanup(opts, r);
			opts.success && opts.success(r, xhr.responseText);
		},
		error: function(xhr, textStatus) {
			wn.request.cleanup(opts, {});
			show_alert(wn._("Unable to complete request: ") + textStatus)
			opts.error && opts.error(xhr)
		}
	};

	if(opts.progress_bar) {
		var interval = null;
		$.extend(ajax_args, {
			xhr: function() {
				var xhr = jQuery.ajaxSettings.xhr();
				interval = setInterval(function() {
					if(xhr.readyState > 2) {
				    	var total = parseInt(xhr.getResponseHeader('Original-Length') || 0) || 
							parseInt(xhr.getResponseHeader('Content-Length'));
				    	var completed = parseInt(xhr.responseText.length);
						var percent = (100.0 / total * completed).toFixed(2);
						opts.progress_bar.css('width', (percent < 10 ? 10 : percent) + '%');
					}
				}, 50);
				wn.last_xhr = xhr;
				return xhr;
			},
			complete: function() {
				opts.progress_bar.css('width', '100%');
				clearInterval(interval);
			}
		})
	}
		
	$.ajax(ajax_args);
}

// call execute serverside request
wn.request.prepare = function(opts) {
	// btn indicator
	if(opts.btn) $(opts.btn).set_working();
	
	// navbar indicator
	if(opts.show_spinner) wn.set_loading();
	
	// freeze page
	if(opts.freeze) wn.dom.freeze();
	
	// no cmd?
	if(!opts.args.cmd) {
		console.log(opts)
		throw "Incomplete Request";
	}
}

wn.request.cleanup = function(opts, r) {
	// stop button indicator
	if(opts.btn) $(opts.btn).done_working();
	
	// hide button indicator
	if(opts.show_spinner) wn.done_loading();

	// un-freeze page
	if(opts.freeze) wn.dom.unfreeze();

	// session expired?
	if(r.session_expired) { 
		if(!wn.app.logged_out) {
			msgprint(wn._('Session Expired. Logging you out'));
			wn.app.logout();		
		}
		return;
	}
	
	// show messages
	if(r.server_messages) {
		r.server_messages = JSON.parse(r.server_messages)
		msgprint(r.server_messages);
	}
	
	// show errors
	if(r.exc) { 
		r.exc = JSON.parse(r.exc);
		if(r.exc instanceof Array) {
			$.each(r.exc, function(i, v) {
				if(v)console.log(v);
			})
		} else {
			console.log(r.exc); 			
		}
	};
	
	if(r['403']) {
		wn.container.change_to('403');
	}

	if(r.docs) {
		wn.model.sync(r.docs);
	}
	if(r.__messages) {
		$.extend(wn._messages, r.__messages);
	}
	
	wn.last_response = r;
}