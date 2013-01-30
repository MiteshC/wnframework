# all country info
from __future__ import unicode_literals

import os, json, webnotes

def get_country_info(country=None):
	data = get_all()
	data = webnotes._dict(data.get(country, {}))
	if not 'date_format' in data:
		data.date_format = "dd-mm-yyyy"
			
	return data

@webnotes.whitelist()
def get_all():
	with open(os.path.join(os.path.dirname(__file__), "country_info.json"), "r") as local_info:
		all_data = json.loads(local_info.read())
	return all_data

def update():
	with open(os.path.join(os.path.dirname(__file__), "currency_info.json"), "r") as nformats:
		nformats = json.loads(nformats.read())
		
	all_data = get_all()
	
	for country in all_data:
		data = all_data[country]
		data["number_format"] = nformats.get(data.get("currency", "default"), 
			nformats.get("default"))["display"]
	
	print all_data
	
	with open(os.path.join(os.path.dirname(__file__), "country_info.json"), "w") as local_info:
		local_info.write(json.dumps(all_data, indent=1))
