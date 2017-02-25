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

import urllib
import utils

try:
	import xbmc, xbmcgui, xbmcplugin
except ImportError:
	pass

def play(url, nid):
	utils.log('play: ' + urllib.quote(url))

	if nid == 'live':
		meta = utils.get_metadata(nid)

		# this is usually the live stream isn't currently active
		if 'error_msg' in meta:
			utils.log('cannot play stream: %s, %s' % (url, meta['error_msg']))
			utils.dialog_error(meta['error_msg'])
			return

	"""
	# XXX disabled as not currently working?

	# permission dance. if we're already logged in (have a valid cookie), no need to log in again
	perms = utils.get_perms(nid)

	if not perms:
		# login and recheck video permissions
		if not utils.wsbk_login():
			return

		perms = utils.get_perms(nid)
		if not perms:
			# we really mustn't have permission
			utils.log('no permission for video %s' % nid)
			utils.dialog_error('No permission to access this video. Check login details in plugin settings.')
			return
	"""

	(stream_url, meta) = utils.get_stream_url(nid)
	listitem = xbmcgui.ListItem(label=meta['title'], iconImage=meta['thumbnail_url'], thumbnailImage=meta['thumbnail_url'])

	utils.log("Playing stream: %s" % stream_url)

	try:
		xbmc.Player().play(stream_url, listitem)
	except:
		utils.dialog_error("Cannot play video")
