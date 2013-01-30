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

import webnotes
import os

from webnotes.utils import now, cint
msgprint = webnotes.msgprint

class DocType:
	def __init__(self, doc=None, doclist=[]):
		self.doc = doc
		self.doclist = doclist

	def change_modified_of_parent(self):
		sql = webnotes.conn.sql
		parent_list = sql('SELECT parent from tabDocField where fieldtype="Table" and options="%s"' % self.doc.name)
		for p in parent_list:
			sql('UPDATE tabDocType SET modified="%s" WHERE `name`="%s"' % (now(), p[0]))

	def scrub_field_names(self):
		restricted = ('name','parent','idx','owner','creation','modified','modified_by','parentfield','parenttype')
		for d in self.doclist:
			if d.parent and d.fieldtype:
				if (not d.fieldname):
					if d.label:
						d.fieldname = d.label.strip().lower().replace(' ','_')
						if d.fieldname in restricted:
							d.fieldname = d.fieldname + '1'
					else:
						d.fieldname = d.fieldtype.lower().replace(" ","_") + "_" + str(d.idx)
						
	
	def set_version(self):
		self.doc.version = cint(self.doc.version) + 1
	
	def validate_series(self, autoname=None, name=None):
		sql = webnotes.conn.sql
		if not autoname: autoname = self.doc.autoname
		if not name: name = self.doc.name
		
		if not autoname and self.doclist.get({"fieldname":"naming_series"}):
			self.doc.autoname = "naming_series:"
		
		if autoname and (not autoname.startswith('field:')) and (not autoname.startswith('eval:')) \
			and (not autoname=='Prompt') and (not autoname.startswith('naming_series:')):
			prefix = autoname.split('.')[0]
			used_in = sql('select name from tabDocType where substring_index(autoname, ".", 1) = %s and name!=%s', (prefix, name))
			if used_in:
				msgprint('<b>Series already in use:</b> The series "%s" is already used in "%s"' % (prefix, used_in[0][0]), raise_exception=1)

	def validate(self):
		for c in [".", "/", "#", "&", "=", ":", "'", '"']:
			if c in self.doc.name:
				webnotes.msgprint(c + " not allowed in name", raise_exception=1)
		self.validate_series()
		self.scrub_field_names()
		validate_fields(self.doclist.get({"doctype":"DocField"}))
		validate_permissions(self.doclist.get({"doctype":"DocPerm"}))
		self.set_version()

	def on_update(self):
		self.make_amendable()
		self.make_file_list()
		
		sql = webnotes.conn.sql
		# make schma changes
		from webnotes.model.db_schema import updatedb
		updatedb(self.doc.name)

		self.change_modified_of_parent()
		
		import conf
		from webnotes.modules.import_merge import in_transfer

		if (not in_transfer) and getattr(conf,'developer_mode', 0):
			self.export_doc()
			self.make_controller_template()

		webnotes.clear_cache(doctype=self.doc.name)

		
	def export_doc(self):
		from webnotes.modules.export_file import export_to_files
		export_to_files(record_list=[['DocType', self.doc.name]])
		
	def import_doc(self):
		from webnotes.modules.import_module import import_from_files
		import_from_files(record_list=[[self.doc.module, 'doctype', self.doc.name]])		

	def make_controller_template(self):
		from webnotes.modules import get_doc_path, get_module_path, scrub
		
		pypath = os.path.join(get_doc_path(self.doc.module, 
			self.doc.doctype, self.doc.name), scrub(self.doc.name) + '.py')

		if not os.path.exists(pypath):
			with open(pypath, 'w') as pyfile:
				with open(os.path.join(get_module_path("core"), "doctype", "doctype", 
					"doctype_template.py"), 'r') as srcfile:
					pyfile.write(srcfile.read())
	
	def make_file_list(self):
		"""
			if allow_attach is checked and the column file_list doesn't exist,
			create a new field 'file_list'
		"""
		if self.doc.allow_attach:
			import webnotes.model.doctype
			temp_doclist = webnotes.model.doctype.get(self.doc.name)
			if 'file_list' not in [d.fieldname for d in temp_doclist if \
					d.doctype=='DocField']:
				new = self.doc.addchild('fields', 'DocField', self.doclist)
				new.label = 'File List'
				new.fieldtype = 'Text'
				new.fieldname = 'file_list'
				new.hidden = 1
				new.permlevel = 0
				new.print_hide = 1
				new.no_copy = 1
				idx_list = [d.idx for d in temp_doclist if d.idx]
				max_idx = idx_list and max(idx_list) or 0
				new.idx = max_idx + 1
				new.save()

	def make_amendable(self):
		"""
			if is_submittable is set, add amended_from
			docfields
		"""
		if self.doc.is_submittable:
			import webnotes.model.doctype
			temp_doclist = webnotes.model.doctype.get(self.doc.name)
			max_idx = max([d.idx for d in temp_doclist if d.idx])
			max_idx = max_idx and max_idx or 0
			if 'amended_from' not in [d.fieldname for d in temp_doclist if \
					d.doctype=='DocField']:
				new = self.doc.addchild('fields', 'DocField', self.doclist)
				new.label = 'Amended From'
				new.fieldtype = 'Link'
				new.fieldname = 'amended_from'
				new.options = "Sales Invoice"
				new.permlevel = 1
				new.print_hide = 1
				new.no_copy = 1
				new.idx = max_idx + 1
				new.save()
				max_idx += 1

def validate_fields_for_doctype(doctype):
	from webnotes.model.doctype import get
	validate_fields(get(doctype, cached=False).get({"parent":doctype, 
		"doctype":"DocField"}))
		
def validate_fields(fields):
	def check_illegal_characters(fieldname):
		for c in ['.', ',', ' ', '-', '&', '%', '=', '"', "'", '*', '$', 
			'(', ')', '[', ']', '/']:
			if c in fieldname:
				webnotes.msgprint("'%s' not allowed in fieldname (%s)" % (c, fieldname))
	
	def check_unique_fieldname(fieldname):
		duplicates = filter(None, map(lambda df: df.fieldname==fieldname and str(df.idx) or None, fields))
		if len(duplicates) > 1:
			webnotes.msgprint('Fieldname <b>%s</b> appears more than once in rows (%s). Please rectify' \
			 	% (fieldname, ', '.join(duplicates)), raise_exception=1)
	
	def check_illegal_mandatory(d):
		if d.fieldtype in ('HTML', 'Button', 'Section Break', 'Column Break') and d.reqd:
			webnotes.msgprint('%(label)s [%(fieldtype)s] cannot be mandatory' % d.fields, 
				raise_exception=1)
	
	def check_link_table_options(d):
		if d.fieldtype in ("Link", "Table"):
			if not d.options:
				webnotes.msgprint("""#%(idx)s %(label)s: Options must be specified for Link and Table type fields""" % d.fields, 
					raise_exception=1)
			if d.options=="[Select]":
				return
			if not webnotes.conn.exists("DocType", d.options):
				webnotes.msgprint("""#%(idx)s %(label)s: Options %(options)s must be a valid "DocType" for Link and Table type fields""" % d.fields, 
					raise_exception=1)

	def check_hidden_and_mandatory(d):
		if d.hidden and d.reqd:
			webnotes.msgprint("""#%(idx)s %(label)s: Cannot be hidden and mandatory (reqd)""" % d.fields,
				raise_exception=True)

	def check_max_items_in_list(fields):
		count = 0
		for d in fields:
			if d.in_list_view: count+=1
		if count > 5:
			webnotes.msgprint("""Max 5 Fields can be set as 'In List View', please unselect a field before selecting a new one.""")
				
	def check_width(d):
		if d.fieldtype == "Currency" and cint(d.width) < 100:
			webnotes.msgprint("Minimum width for FieldType 'Currency' is 100px", raise_exception=1)

	for d in fields:
		if not d.permlevel: d.permlevel = 0
		if not d.fieldname:
			webnotes.msgprint("Fieldname is mandatory in row %s" % d.idx, raise_exception=1)
		check_illegal_characters(d.fieldname)
		check_unique_fieldname(d.fieldname)
		check_illegal_mandatory(d)
		check_link_table_options(d)
		check_hidden_and_mandatory(d)

def validate_permissions_for_doctype(doctype, for_remove=False):
	from webnotes.model.doctype import get
	validate_permissions(get(doctype, cached=False).get({"parent":doctype, 
		"doctype":"DocPerm"}), for_remove)

def validate_permissions(permissions, for_remove=False):
	doctype = permissions and permissions[0].parent
	issingle = issubmittable = False
	if doctype:
		issingle = webnotes.conn.get_value("DocType", doctype, "issingle")
		issubmittable = webnotes.conn.get_value("DocType", doctype, "is_submittable")
			
	def get_txt(d):
		return "For %s (level %s) in %s row %s:" % (d.role, d.permlevel, d.parent, d.idx)
		
	def check_atleast_one_set(d):
		if not d.read and not d.write and not d.submit and not d.cancel and not d.create:
			webnotes.msgprint(get_txt(d) + " Atleast one of Read, Write, Create, Submit, Cancel must be set.",
			 	raise_exception=True)
		
	def check_double(d):
		similar = permissions.get({
			"role":d.role,
			"permlevel":d.permlevel,
			"match": d.match
		})
		
		if len(similar) > 1:
			webnotes.msgprint(get_txt(d) + " Only one rule allowed for a particular Role and Level.", 
				raise_exception=True)
	
	def check_level_zero_is_set(d):
		if cint(d.permlevel) > 0 and d.role != 'All':
			if not permissions.get({"role": d.role, "permlevel": 0}):
				webnotes.msgprint(get_txt(d) + " Higher level permissions are meaningless if level 0 permission is not set.",
					raise_exception=True)
					
			if d.create or d.submit or d.cancel or d.amend or d.match: 
				webnotes.msgprint("Create, Submit, Cancel, Amend, Match has no meaning at level " + d.permlevel,
					raise_exception=True)
	
	def check_permission_dependency(d):
		if d.write and not d.read:
			webnotes.msgprint(get_txt(d) + " Cannot set Write permission if Read is not set.",
				raise_exception=True)
		if (d.submit or d.cancel or d.amend) and not d.write:
			webnotes.msgprint(get_txt(d) + " Cannot set Submit, Cancel, Amend permission if Write is not set.",
				raise_exception=True)
		if d.amend and not d.write:
			webnotes.msgprint(get_txt(d) + " Cannot set Amend if Cancel is not set.",
				raise_exception=True)
	
	def remove_report_if_single(d):
		if d.report and issingle:
			webnotes.msgprint(doctype + " is a single DocType, permission of type Report is meaningless.")
	
	def check_if_submittable(d):
		if d.submit and not issubmittable:
			webnotes.msgprint(doctype + " is not Submittable, cannot assign submit rights.",
				raise_exception=True)
	
	for d in permissions:
		if not d.permlevel: 
			d.permlevel=0
		check_atleast_one_set(d)
		if not for_remove:
			check_double(d)
			check_permission_dependency(d)
			check_if_submittable(d)
		check_level_zero_is_set(d)
		remove_report_if_single(d)
