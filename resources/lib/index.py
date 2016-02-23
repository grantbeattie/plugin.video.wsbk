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

import json, sys, re, time
import utils
from bs4 import BeautifulSoup

try:
	import xbmc, xbmcgui, xbmcplugin
except ImportError:
	pass

def scrape_season_list():
	season_list = []

	html = utils.http_get("/en/videos/all_videos/")
	soup = BeautifulSoup(html)
	for year in soup.find("select", id="season_year").find_all("option"):
		if year.attrs['value'] != "":
			season_list.append(year.text)

	return season_list


def top_index():
	addon_handle = int(sys.argv[1])

	url = utils.build_url({ 'play': '/en/live/', 'nid': 'live' })
	listitem = xbmcgui.ListItem(label='Live stream')
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=listitem, isFolder=False)

	for sid in scrape_season_list():
		url = utils.build_url({ 'sid': sid })
		listitem = xbmcgui.ListItem(label=sid)
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=listitem, isFolder=True)

	xbmcplugin.endOfDirectory(addon_handle)
	xbmcplugin.setContent(addon_handle, content='tvshows')

def get_xbmc_videoInfo(v):
		info = {}
		info['title'] = v['title']
		info['aired'] = time.strftime('%Y-%m-%d', v['date'])
		return info

def get_xbmc_videoStreamInfo():
	return {
		'codec':	'h264'
	}

def get_xbmc_audioStreamInfo():
	return {
		'codec':	'aac',
		'language':	'en',
		'channels':	2
	}

def get_vid_list_url(sid="", eid="", category="", vtid="", before=""):
	# category, season, event, type, before
	vids_url = "/en/videos/all_videos/ajax/list_all%s?champ=undefined&category_btn%%5B%%5D=%s&sid=%s&url_mode=list_all&eid=%s%s"

	# /en/videos/all_videos/ajax/list_all_before/14434_1402221780?champ=undefined&category_btn%5B%5D=sbk&sid=2014&url_mode=list_all&eid=&vtid%5B%5D=6
	vtid_str = ''
	if vtid != '':
		vtid_str = "&vtid%%5B%%5D=%s" % vtid

	before_str = ''
	if before != '':
		before_str = '_before/' + before

	url = vids_url % (before_str, category, sid, eid, vtid_str)
	return url

def scrape_vids(html):
	#<li id=\"all_video_12655_1393059180\" class=\"all_video label_e_plus\" >\n    <a href=\"http:\/\/www.worldsbk.com\/en\/videos\/2014\/Guintoli on first pole of the year in Australia?from_list=all_videos\"><span class=\"thumb\"><img src=\"http:\/\/photos.worldsbk.com\/2014\/02\/22\/guintoli_thumb_big.jpg\" alt=\"\"><\/span><\/a>\n    <div class=\"title sbk\">\n      <h2>Guintoli on first pole of the year in Australia<\/h2>\n      <footer class=\"date\">Saturday, 22 February  8:53<\/footer>\n    <\/div>\n<\/li>

	vids = []
	soup = BeautifulSoup(html)
	for vid in soup.find_all("li"):
		v = {}
		v['attrs'] = vid.attrs
		v['id'] = re.sub('^all_videos?_', '', vid.attrs['id'])
		v['nid'] = re.sub('_\d+', '', v['id'])
		v['date'] = time.gmtime(float(re.sub('\d+_', '', v['id'])))
		url = re.sub('\?.*', '', vid.find("a").get("href"))
		url = re.sub('\?.*', '', url)
		v['url'] = re.sub('.*?/en', '/en', url)
		v['thumbnail'] = vid.find("img").attrs['src']
		if vid.find("div").find("h2") is not None:
			v['title'] = vid.find("div").find("h2").text
		elif vid.find("div").find("h3") is not None:
			v['title'] = vid.find("div").find("h3").text

		if 'label_e_premium' in v['attrs']['class']:
			v['listtitle'] = '(E) ' + v['title']
		elif 'label_e_plus' in v['attrs']['class']:
			v['listtitle'] = '(VP) ' + v['title']
		else:
			v['listtitle'] = v['title']

		vids.append(v)

	return vids


# retreive all videos for the given parameters - requests "next page" until no more
def get_vids(sid="", eid="", category="", vtid=""):
	vids = []
	vid_list_url = get_vid_list_url(sid=sid, category=category, vtid=vtid)
	res = utils.http_get(vid_list_url)
	json_data = json.load(res)

	status = int(json_data['status'])
	while status == 0: # more to fetch
		vids.extend(scrape_vids(json_data['html']))
		last_id = vids[-1]['id']
		vid_list_url = get_vid_list_url(sid=sid, category=category, vtid=vtid, before=last_id)
		res = utils.http_get(vid_list_url)
		json_data = json.load(res)
		status = int(json_data['status'])

	return vids

def build_index(sid="", eid="", category="", vtid=""):
	addon_handle = int(sys.argv[1])

	if sid == "":
		top_index()

	# event eg. Phillip Island
	#if eid == "":

	elif category == "":
		cat_list = [
			('Superbike', 'sbk'),
			('Supersport', 'ssp'),
			('Superstock 1000', 'stk'),
			('Superstock 600', 'st6'),
			('European Junior Cup', 'ejc')
		]

		for (i, cat) in enumerate(cat_list):
			url = utils.build_url({ 'sid': sid, 'category': cat_list[i][1]})
			listitem = xbmcgui.ListItem(label=cat_list[i][0])
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=listitem, isFolder=True)

		xbmcplugin.endOfDirectory(addon_handle)
		xbmcplugin.setContent(addon_handle, content='tvshows')


	elif vtid == "":
		vtid_list = [
			('Full sessions', 6),
			('Highlights', 5),
			('Features', 2),
			('Interviews', 1),
			('Season review', 17),
		]

		for (i, vt) in enumerate(vtid_list):
			url = utils.build_url({ 'sid': sid, 'category': category, 'vtid': vtid_list[i][1]})
			listitem = xbmcgui.ListItem(label=vtid_list[i][0])
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=listitem, isFolder=True)

		xbmcplugin.endOfDirectory(addon_handle)
		xbmcplugin.setContent(addon_handle, content='tvshows')


	else:
		vids = get_vids(sid=sid, category=category, vtid=vtid)

		for v in vids:
			thumbnail_url = v['thumbnail']
			url = utils.build_url({ 'play': v['url'], 'nid': v['nid'] })
			listitem = xbmcgui.ListItem(label=v['listtitle'], iconImage=thumbnail_url, thumbnailImage=thumbnail_url)

			listitem.setInfo('video', get_xbmc_videoInfo(v))
			listitem.addStreamInfo('audio', get_xbmc_audioStreamInfo())
			listitem.addStreamInfo('video', get_xbmc_videoStreamInfo())
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=listitem, isFolder=True)

		xbmcplugin.endOfDirectory(addon_handle)
		xbmcplugin.setContent(addon_handle, content='episodes')
