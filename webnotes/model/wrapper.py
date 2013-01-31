# Copyright (c) 2012 Web Notes Technologies Pvt Ltd (http://erpnext.com)
# 
# MIT License (MIT)
# 
# Permission is hereby granted, free of charge, to any person obtaining a 
# copy of this software and associated documentation files (the "Software"), 
# to deal in the Software without restriction, including without limitation 
# the rights to use, copy, modify, merge, publish, distribute, sublicense, 
# and/or sell copies of the Software, and to permit persons to whom the 
# Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 

from __future__ import unicode_literals
##	Transactions are defined as collection of classes, a ModelWrapper represents collection of Document<br />
#	objects for a transaction with main and children.
#
#	Group actions like save, etc are performed on doclists.
#	@package webnotes

import webnotes
from webnotes import _
from webnotes.utils import cint
from webnotes.model.doc import Document

##	Collection of Documents with one parent and multiple children
class ModelWrapper:
	##	ModelWrapper constructor<br />
	#	
	#	@see load_from_db()
	#	@see set_doclist()
	#
	#	@param dt doctype(default None)
	#	@param dn doc name(default None)
	def __init__(self, dt=None, dn=None):
		self.docs = []
		self.obj = None
		self.to_docstatus = 0
		self.ignore_permissions = 0
		if isinstance(dt, basestring) and not dn:
			dn = dt
		if dt and dn:
			self.load_from_db(dt, dn)
		elif isinstance(dt, list):
			self.set_doclist(dt)
		elif isinstance(dt, dict):
			self.set_doclist([dt])
			
	##	Load doclist from dt
	#	
	#	@see set_doclist()
	#	@see run_method()
	#
	#	@param dt The DocType on which need the data(default None)
	#	@param dn The DocName on which need the data(default None)
	#	@param prefix It is the prefix to table name (default tab)
	def load_from_db(self, dt=None, dn=None, prefix='tab'):
		
		from webnotes.model.doc import Document, getchildren

		if not dt: dt = self.doc.doctype
		if not dn: dn = self.doc.name

		doc = Document(dt, dn, prefix=prefix)

		# get all children types
		tablefields = webnotes.model.meta.get_table_fields(dt)

		# load chilren
		doclist = webnotes.doclist([doc,])
		for t in tablefields:
			doclist += getchildren(doc.name, t[0], t[1], dt, prefix=prefix)

		self.set_doclist(doclist)
		self.run_method("onload")

	##	Make this iterable
	#
	#	@return <code>self.docs.__iter__()</code>
	def __iter__(self):
		
		return self.docs.__iter__()

	##	Expand called from client
	#
	#	@param data The data to expand
	#	@see set_doclist()
	def from_compressed(self, data, docname):
		
		from webnotes.model.utils import expand
		self.docs = expand(data)
		self.set_doclist(self.docs)
		
	def set_doclist(self, docs):
		for i, d in enumerate(docs):
			if isinstance(d, dict):
				docs[i] = Document(fielddata=d)
		
		self.docs = self.doclist = webnotes.doclist(docs)
		self.doc, self.children = self.doclist[0], self.doclist[1:]
		if self.obj:
			self.obj.doclist = self.doclist
			self.obj.doc = self.doc
	
	##	Create a DocType object
	#	
	#	@return DocType Object
	def make_obj(self):
		
		if self.obj: return self.obj

		from webnotes.model.code import get_obj
		self.obj = get_obj(doc=self.doc, doclist=self.doclist)
		return self.obj

	##	return as a list of dictionaries
	#
	#	@return list of dictionaries
	def to_dict(self):
		return [d.fields for d in self.docs]

	##	Raises exception if the modified time is not the same as in the database
	#	
	def check_if_latest(self):
		
		from webnotes.model.meta import is_single

		if (not is_single(self.doc.doctype)) and (not cint(self.doc.fields.get('__islocal'))):
			tmp = webnotes.conn.sql("""
				SELECT modified FROM `tab%s` WHERE name="%s" for update"""
				% (self.doc.doctype, self.doc.name))

			if not tmp:
				webnotes.msgprint("""This record does not exist. Please refresh.""", raise_exception=1)

			if tmp and str(tmp[0][0]) != str(self.doc.modified):
				webnotes.msgprint("""
				Document has been modified after you have opened it.
				To maintain the integrity of the data, you will not be able to save your changes.
				Please refresh this document. [%s/%s]""" % (tmp[0][0], self.doc.modified), raise_exception=1)

	def check_links(self):
		ref, err_list = {}, []
		for d in self.docs:
			if not ref.get(d.doctype):
				ref[d.doctype] = d.make_link_list()

			err_list += d.validate_links(ref[d.doctype])

		if err_list:
			webnotes.msgprint("""[Link Validation] Could not find the following values: %s.
			Please correct and resave. Document Not Saved.""" % ', '.join(err_list), raise_exception=1)

	def update_timestamps_and_docstatus(self):
		from webnotes.utils import now
		ts = now()
		user = webnotes.__dict__.get('session', {}).get('user') or 'Administrator'

		for d in self.docs:
			if self.doc.fields.get('__islocal'):
				d.owner = user
				d.creation = ts

			d.modified_by = user
			d.modified = ts
			if d.docstatus != 2 and self.to_docstatus >= d.docstatus: # don't update deleted
				d.docstatus = self.to_docstatus

	def prepare_for_save(self, check_links):
		self.check_if_latest()
		if check_links:
			self.check_links()
		self.update_timestamps_and_docstatus()
		self.update_parent_info()
		
	def update_parent_info(self):
		idx_map = {}
		is_local = cint(self.doc.fields.get("__islocal"))
		
		for i, d in enumerate(self.doclist[1:]):
			if d.parentfield:
				d.parenttype = self.doc.doctype
				d.parent = self.doc.name
			if not d.idx:
				d.idx = idx_map.setdefault(d.parentfield, 0) + 1
			if is_local:
				# if parent is new, all children should be new
				d.fields["__islocal"] = 1
			
			idx_map[d.parentfield] = d.idx
	##	This method runs the python function within specific DocType<br/>
	#	This will check if the python function declared in DocType or not, otherwise it will call given method with <code>custom_</code> prefix.
	#
	#	@param method The name of method to be called
	def run_method(self, method):
		self.make_obj()
		if hasattr(self.obj, method):
			getattr(self.obj, method)()
		if hasattr(self.obj, 'custom_' + method):
			getattr(self.obj, 'custom_' + method)()

		notify(self.obj, method)
		
		self.set_doclist(self.obj.doclist)

	def save_main(self):
		try:
			self.doc.save(cint(self.doc.fields.get('__islocal')))
		except NameError, e:
			webnotes.msgprint('%s "%s" already exists' % (self.doc.doctype, self.doc.name))

			# prompt if cancelled
			if webnotes.conn.get_value(self.doc.doctype, self.doc.name, 'docstatus')==2:
				webnotes.msgprint('[%s "%s" has been cancelled]' % (self.doc.doctype, self.doc.name))
			webnotes.errprint(webnotes.utils.getTraceback())
			raise e

	def save_children(self):
		child_map = {}
		for d in self.children:
			if d.fields.get("parent") or d.fields.get("parentfield"):
				d.parent = self.doc.name # rename if reqd
				d.parenttype = self.doc.doctype
				
				d.save(new = cint(d.fields.get('__islocal')))
			
			child_map.setdefault(d.doctype, []).append(d.name)
		
		# delete all children in database that are not in the child_map
		
		# get all children types
		tablefields = webnotes.model.meta.get_table_fields(self.doc.doctype)
				
		for dt in tablefields:
			cnames = child_map.get(dt[0]) or []
			if cnames:
				webnotes.conn.sql("""delete from `tab%s` where parent=%s and parenttype=%s and
					name not in (%s)""" % (dt[0], '%s', '%s', ','.join(['%s'] * len(cnames))), 
						tuple([self.doc.name, self.doc.doctype] + cnames))
			else:
				webnotes.conn.sql("""delete from `tab%s` where parent=%s and parenttype=%s""" \
					% (dt[0], '%s', '%s'), (self.doc.name, self.doc.doctype))
	##	This function inserting the doc fields
	#	
	#	@see save()
	#	@return save method 
	def insert(self):
		self.doc.fields["__islocal"] = 1
		return self.save()
		
	##	This method gives the read permission
	#
	#	@return <code>webnotes.has_permission</code>
	def has_read_perm(self):
		return webnotes.has_permission(self.doc.doctype, "read", self.doc)
		
	##	This method checks the permission to write if it has then calls the another methods for saving data<br />
	#	else display the message no permission to write
	#
	#	@return <code>self</code>object
	#	@see prepare_for_save()
	#	@see run_method()
	#	@see save_main()
	#	@see save_children()
	#	@see no_permission_to()
	def save(self, check_links=1):
		if self.ignore_permissions or webnotes.has_permission(self.doc.doctype, "write", self.doc):
			self.prepare_for_save(check_links)
			workflowTransition = []
			if self.doc.workflow_state:
				previousState = webnotes.conn.get_value(self.doc.doctype, self.doc.name, 'workflow_state')
				if previousState<>self.doc.workflow_state:
					workflowTransition = webnotes.conn.sql("""select `tabWorkflow Transition`.`pre_function`, `tabWorkflow Transition`.`post_function` from `tabWorkflow Transition` left join `tabWorkflow` on (`tabWorkflow`.name=`tabWorkflow Transition`.parent) where `tabWorkflow Transition`.`state`="%s" and `tabWorkflow Transition`.`next_state`="%s" and `tabWorkflow`.`is_active`=1 """%(previousState,self.doc.workflow_state))
					wfStatePreCheck = webnotes.conn.sql("""SELECT  `tabWorkflow Document State`.`pre_check` FROM  `tabWorkflow Document State` LEFT JOIN  `tabWorkflow` ON (  `tabWorkflow`.name =  `tabWorkflow Document State`.parent ) WHERE  `tabWorkflow Document State`.`state` =  "%s" AND  `tabWorkflow`.`is_active` =1 """%(self.doc.workflow_state))
					if len(wfStatePreCheck)>0 and wfStatePreCheck[0][0] is not None:
						self.run_method(wfStatePreCheck[0][0])
			self.run_method('validate')
			if len(workflowTransition)==1 and workflowTransition[0][0]<>"" and workflowTransition[0][0] is not None:
				self.run_method(workflowTransition[0][0])
			self.save_main()
			self.save_children()
			self.run_method('on_update')
			if len(workflowTransition)==1  and workflowTransition[0][1]<>"" and workflowTransition[0][1] is not None:
				self.run_method(workflowTransition[0][1])
		else:
			self.no_permission_to(_("Write"))
		
		return self
		
	##	This method first check the permission for submit<br />
	#	If it has then save the data
	#	If it not raise the exception
	#
	#	@see save()
	#	@see run_method()
	#	@return self object
	def submit(self):
		if self.ignore_permissions or webnotes.has_permission(self.doc.doctype, "submit", self.doc):
			if self.doc.docstatus != 0:
				webnotes.msgprint("Only draft can be submitted", raise_exception=1)
			self.to_docstatus = 1
			self.save()
			self.run_method('on_submit')
		else:
			self.no_permission_to(_("Submit"))
			
		return self
	
	##	This method cansceling the submitted doc
	#
	#	@see prepare_for_save()
	#	@see save_main()
	#	@see save_children()
	#	@see run_method()
	#	@see no_permission_to()
	#	@return self object
	def cancel(self):
		if self.ignore_permissions or webnotes.has_permission(self.doc.doctype, "cancel", self.doc):
			if self.doc.docstatus != 1:
				webnotes.msgprint("Only submitted can be cancelled", raise_exception=1)
			self.to_docstatus = 2
			self.prepare_for_save(1)
			self.save_main()
			self.save_children()
			self.run_method('on_cancel')
		else:
			self.no_permission_to(_("Cancel"))
			
		return self
		
	##	This method update the data of the submitted doc
	#
	#	@see prepare_for_save()
	#	@see save_main()
	#	@see save_children()
	#	@see run_method()
	#	@see no_permission_to()
	#	@return self object
	def update_after_submit(self):
		if self.doc.docstatus != 1:
			webnotes.msgprint("Only to called after submit", raise_exception=1)
		if self.ignore_permissions or webnotes.has_permission(self.doc.doctype, "write", self.doc):
			self.to_docstatus = 1
			self.prepare_for_save(1)
			self.save_main()
			self.save_children()
			self.run_method('on_update_after_submit')
		else:
			self.no_permission_to(_("Update"))
		
		return self
	## This method used to display the message for no permission
	#
	def no_permission_to(self, ptype):
		webnotes.msgprint(("%s (%s): " % (self.doc.name, _(self.doc.doctype))) + \
			_("No Permission to ") + ptype, raise_exception=True)

	##	Copy previous invoice and change dates
	#
	#	@param source_wrapper The source_wrapper
	#	@return <code>new_wrapper</code>
def clone(source_wrapper):
	if isinstance(source_wrapper, list):
		source_wrapper = ModelWrapper(source_wrapper)
	
	new_wrapper = ModelWrapper(source_wrapper.doclist.copy())
	new_wrapper.doc.fields.update({
		"amended_from": None,
		"amendment_date": None,
	})
	
	for d in new_wrapper.doclist:
		d.fields.update({
			"name": None,
			"__islocal": 1,
			"docstatus": 0,
		})
	
	return new_wrapper


def notify(controller, caller_method):
	try:
		from startup.observers import observer_map
	except ImportError:
		return
		
	doctype = controller.doc.doctype
	
	def call_observers(key):
		if key in observer_map:
			observer_list = observer_map[key]
			if isinstance(observer_list, basestring):
				observer_list = [observer_list]
			for observer_method in observer_list:
				webnotes.get_method(observer_method)(controller, caller_method)
	
	call_observers("*:*")
	call_observers(doctype + ":*")
	call_observers("*:" + caller_method)
	call_observers(doctype + ":" + caller_method)

	##Return child records of a particular type
	#
	#	@param doclist The DocList which is used to copy 
	#	@param parentfield The ParentFild which is need to get list
	#	@return <code>webnotes.model.utils.getlist</code>
def getlist(doclist, parentfield):
	
	import webnotes.model.utils
	return webnotes.model.utils.getlist(doclist, parentfield)
	
	##	Make a copy of the doclist
	#
	#	@param doclist The DocList which is used to copy 
	#	@param no_copy The No of Copy of the doc
	#	@return <code>webnotes.model.utils.copy_doclist</code>
def copy_doclist(doclist, no_copy = []):
	
	import webnotes.model.utils
	return webnotes.model.utils.copy_doclist(doclist, no_copy)

