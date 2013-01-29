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

##
#
#	@package webnotes

from __future__ import unicode_literals
import webnotes

workflow_names = {}
##	This method for set the workflow name
#
#	@param doctype The DocType which is need to get workflow name
#	@return <code>workflow_names</code>
def get_workflow_name(doctype):
	global workflow_names
	if not doctype in workflow_names:
		workflow_name = webnotes.conn.get_value("Workflow", {"document_type": doctype, 
			"is_active": "1"}, "name")
	
		# no active? get default workflow
		if not workflow_name:
			workflow_name = webnotes.conn.get_value("Workflow", {"document_type": doctype}, 
			"name")
				
		workflow_names[doctype] = workflow_name
			
	return workflow_names[doctype]

##	This method for set the workflow state
#
#	@param doctype The DocType which is need to get workflow default state
#	@return <code>workflow document state</code>
def get_default_state(doctype):
	workflow_name = get_workflow_name(doctype)
	return webnotes.conn.get_value("Workflow Document State", {"parent":doctype,
		"idx":1}, "state")

##	This method for set the workflow field name
#
#	@param doctype The DocType which is need to get workflow state fieldname
#	@return <code>workflow state field</code>
def get_state_fieldname(doctype):
	workflow_name = get_workflow_name(doctype)
	return webnotes.conn.get_value("Workflow", workflow_name, "workflow_state_field")