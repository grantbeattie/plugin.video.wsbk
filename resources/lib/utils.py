# Copyright (c) 2016 Grant Beattie <xbmc#grantbeattie.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, os
import urllib, urllib2, cookielib, json, re
import xml.etree.ElementTree as ET
import xbmc, xbmcaddon, xbmcgui

import config

TEMP = os.path.join(xbmc.translatePath('special://temp/'), config.ADDON_ID)
if not os.path.isdir(TEMP):
	os.mkdir(TEMP)

COOKIES = os.path.join(TEMP, 'cookies.txt')

addon = xbmcaddon.Addon(config.ADDON_ID)

def http_get(url, loadcookies = False, savecookies = False):
	log(url)
	cj = cookielib.LWPCookieJar(COOKIES)

	cookie_handler = urllib2.HTTPCookieProcessor(cj)

	proxy_host = addon.getSetting('proxy_host')
	proxy_port = addon.getSetting('proxy_port')
	proxy_username = addon.getSetting('proxy_username')
	proxy_password = addon.getSetting('proxy_password')
	if proxy_host != "" and proxy_port != "":
		if proxy_username != "":
			proxy_url = "http://%s:%s@%s:%s" % (proxy_username, proxy_password, proxy_host, proxy_port)
			proxy_handler = urllib2.ProxyHandler({'http': proxy_url})
			auth = urllib2.HTTPBasicAuthHandler()
			opener = urllib2.build_opener(proxy_handler, auth, cookie_handler)
		else:
			proxy_handler = urllib2.ProxyHandler({'http': "http://%s:%s" % (proxy_host, proxy_port)})
			opener = urllib2.build_opener(proxy_handler, cookie_handler)

		urllib2.install_opener(opener)
	else:
		opener = urllib2.build_opener(cookie_handler)
		urllib2.install_opener(opener)

	req = urllib2.Request(config.base_url + url, headers=config.http_headers)

	if loadcookies is True and os.path.isfile(COOKIES):
		cj.load(ignore_discard = True)
		cj.add_cookie_header(req)

	try:
		r = urllib2.urlopen(req)
	except urllib2.HTTPError as e:
		if hasattr(e, 'reason'):
			log(e)
			dialog_error('%s. Check proxy details in plugin settings.' % e.reason)
			exit(0)
		elif hasattr(e, 'code'):
			log(e.code)
	else:
		pass

	if savecookies is True:
		cj.save(ignore_discard = True)

	return r



def build_url(query):
	base_url = sys.argv[0]
	return base_url + '?' + urllib.urlencode(query)


def log(msg):
	xbmc.log(msg="[%s %s] %s" % (config.NAME, config.VER, msg), level=xbmc.LOGNOTICE)


def isTrue(val):
	if type(val) == type(True): return val
	if str(val).lower() == 'true': return True
	return False


def wsbk_login():
	if addon.getSetting('username') == "" or addon.getSetting('password') == "":
		return True

	login_dict = {
		'name': addon.getSetting('username'),
		'pass': addon.getSetting('password')
	}

	url = '/en/user/login?' + urllib.urlencode(login_dict)

	res = http_get(url, savecookies = True)
	json_data = json.load(res)

	if 'status' in json_data and json_data['status'] != '0':
		dialog_error("Incorrect worldsbk.com username/password. Check login details in plugin settings.")
		log("Login failed")
		return False
	else:
		log("Login successful")
	
	return True


def get_stream_url(nid):
	meta = {}
	if nid == 'live':
		json_url = "/en/video/live/mobile/srcweb/0"
		res = http_get(json_url, loadcookies = True)
		json_data = json.load(res)

		# 0 -> akamai, 1 -> level3
		feed = json_data['live_data'][0]['langs_content']['feeds'][0]
		stream_url = feed['m3u8']
		meta['title'] = 'WorldSBK Live stream'
		meta['thumbnail_url'] = ''

	else:
		json_url = "/en/video/demand/mobile/srcweb/0/%s" % nid
		res = http_get(json_url, loadcookies = True)
		json_data = json.load(res)

		stream_url = ''
		if 'videos' in json_data:
			meta['title'] = json_data['videos'][0]['title']
			meta['thumbnail_url'] = json_data['videos'][0]['urlimage']
			feed = json_data['videos'][0]['video_data'][0]['langs_content'][0]['feeds'][0]
			stream_url = feed['m3u8']

	return (stream_url, meta)


def get_metadata(nid):
	if nid == 'live':
		url = '/en/video/live/meta_hds/0'
	else:
		url = '/en/video/demand/meta_hds/%s' % nid

	res = http_get(url, loadcookies = True)
	root = ET.fromstring(res.read())

	meta = {}
	if 'error_msg' in root.attrib:
		meta['error_msg'] = root.attrib['error_msg']
	#else:
	#	if nid != 'live':
	#		if root.find('video').attrib['title'] is not None: meta['title'] = root.find('video').attrib['title']
	#		if root.find('video').attrib['image_url'] is not None: meta['thumbnail_url'] = root.find('video').attrib['image_url']

	return meta


def get_perms(nid):
	if nid == 'live':
		url = '/en/video/live/perms/0'
	else:
		url = '/en/video/demand/perms/0/%s' % nid

	res = http_get(url, loadcookies = True)
	# live perms json is surrounded by (); which confuses Python json
	json_str = re.sub('(^\(|\);$)', '', res.read())
	json_data = json.loads(json_str)

	if 'permission' in json_data:
		return isTrue(json_data['permission'])
	elif 'perms_user' in json_data:
		return isTrue(json_data['perms_user'])
	else:
		return False


def dialog_error(err):
	dialog = xbmcgui.Dialog()
	msg = []
	msg.append("%s - Error" % config.NAME)
	msg.append(err)
	dialog.ok(*msg)

