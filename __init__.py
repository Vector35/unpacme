#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from base64 import b64decode
from re import A
import requests
import json
import time
import pprint
from pathlib import Path
from binaryninjaui import (UIAction, UIActionHandler, Menu, UIContext)
from PySide6.QtCore import QStandardPaths

from binaryninja.platform import Platform
from binaryninja.plugin import BackgroundTaskThread, PluginCommand
from binaryninja.log import (log_error, log_info, log_warn, log_debug)
from binaryninja.settings import Settings
from binaryninja.interaction import get_text_line_input, show_message_box, get_choice_input
from binaryninja.mainthread import execute_on_main_thread

# Yes, yes, I should use type hints.
# Also, this should be a class.
# Also, it should be a sidebar panel with a history viewer.
# Going for quick and dirty for now.

URL = 'https://api.unpac.me/api/v1'

pluginjson = Path(__file__).with_name("plugin.json")
version = json.load(open(str(pluginjson), 'rb'))['version']

Settings().register_group("unpacme", "UnpacMe")
Settings().register_setting("unpacme.api_key", """
    {
        "title" : "UnpacMe API Key",
        "type" : "string",
        "default" : "",
        "description" : "Register for a free account at https://www.unpac.me/",
        "ignore" : ["SettingsProjectScope", "SettingsResourceScope"]
    }
    """)
dl = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
Settings().register_setting("unpacme.download_folder", '''
    {
        "title" : "UnpacMe Download folder",
        "type" : "string",
        "default" : "''' + dl + '''",
        "description" : "Location where unpacked files from UnpacMe are download. Defaults to user download folder.",
        "ignore" : ["SettingsProjectScope", "SettingsResourceScope"]
    }
    ''')

def valid_key(k):
	try:
		s = b64decode(k)
		return valid_json(s)
	except ValueError:
		return False

def valid_json(s):
	try:
		j = json.loads(s)
	except ValueError:
		return False
	return True

def check_key(key):
	if key == "":
		msg = "Unpac.Me API Key"
		newkey = get_text_line_input(msg, msg)
		if valid_key(newkey.strip()):
			Settings().set_string("unpacme.api_key", newkey)
		else:
			log_error("Does not appear to be a valid UnpacMe key. Please set the proper key in settings or by re-running this plugin.")
			return False
	if valid_key(key):
		return True
	return False

def endpoint():
	key = Settings().get_string("unpacme.api_key")
	if not check_key(key):
		return
	req = requests.session()
	req.headers = {
		'User-Agent': f'Binary Ninja UnpacMe Client v{version}',
		'Authorization': 'Key ' + key
	}
	return req

def download(actioncontext):
	req = endpoint()
	log_info(f"Checking all available downloads")
	cursor = int(time.time())
	history = []
	while True:
		r = req.get(f'{URL}/private/history', params={'cursor': cursor, 'limit': 50}, timeout=10)
		if r.status_code == 404:
			break
		data = r.json()
		if r.status_code == 400:
			log_error(f'Failed due to {data["error"]} : {data["description"]}')
			break
		history += data['results']
		log_debug(pprint.pformat(data['results']))
		cursor = data['cursor']
	choices = [x['sha256'] for x in history]
	choice = get_choice_input("Select History Entry", "Select", choices)
	if choice is None:
		return
	hash = history[choice]['sha256']
	id = history[choice]['id']
	r = req.get(f'{URL}/private/results/{id}', timeout=10)
	if r.status_code != 200:
		log_warn(f"Unable to query status for id {id}")
		return
	if "status" not in r.json().keys(): #Can't combine because need to check property separately
		log_warn(f"Unable to query status for id {id}")
		return
	if r.json()["status"] != "complete":
		log_warn(f"Submission {id} is in status {r.json()['status']}.")
		return
	data = {'value': hash, 'repo_type': "malware"}
	r = req.post(f'{URL}/private/search/term/sha256', json=data, timeout=10)
	childchoices = [hash]
	for result in r.json()['results']:
		for analysis in result['analysis']:
			id = analysis['id']
			r2 = req.get(f'{URL}/private/results/{id}', timeout=10)
			for result2 in r2.json()["results"]:
				childchoices.append(result2["hashes"]["sha256"])
	childchoice = get_choice_input("Select Binary (same again will download original, others are unpacked children)", "Download", childchoices)
	if childchoice is None:
		return
	dlhash = childchoices[childchoice]
	r = req.get(f'{URL}/private/download/{dlhash}', timeout=10)
	if r.status_code != 200:
		log_error(f'Unable to download {URL}/private/download/{dlhash}')
	else:
		dest = Path(Settings().get_string("unpacme.download_folder")) / dlhash
		open(dest, 'wb').write(r.content)
		execute_on_main_thread(lambda: actioncontext.context.openFilename(str(dest)))

def submit(bv):
	req = endpoint()
	log_info(f"Uploading")
	r = req.post(f'{URL}/private/upload', files={'file': bv.parent_view[:]}, timeout=10)

def is_valid(bv):
	if bv.platform in [Platform['windows-x86'], Platform['windows-x86_64']]:
		# Not real MB but not sure how it's being counted, so this seems safer
		if len(bv.parent_view) < (1000*1000*20):
			return True
	return False

PluginCommand.register("UnpacMe\\Submit to Unpac.Me", "Submit Binary to automated UnPac.Me service", submit, is_valid)
UIAction.registerAction("UnpacMe\\Download from Unpac.Me...")
UIActionHandler.globalActions().bindAction("UnpacMe\\Download from Unpac.Me...", UIAction(download))
Menu.mainMenu("Plugins").addAction("UnpacMe\\Download from Unpac.Me...", "UnpacMe")
