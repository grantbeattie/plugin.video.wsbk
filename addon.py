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

import os, sys
import urlparse

try:
        cur_dir = os.path.dirname(os.path.abspath(__file__))
except:
        cur_dir = os.getcwd()

sys.path.append(os.path.join(cur_dir, 'resources', 'lib'))
import index, play

args = urlparse.parse_qs(sys.argv[2][1:])

play_arg = args.get('play', None)
sid_arg = args.get('sid', None)
eid_arg = args.get('eid', None)
category_arg = args.get('category', None)
vtid_arg = args.get('vtid', None)
nid_arg = args.get('nid', None)

if play_arg is not None:
	play.play(url=play_arg[0], nid=nid_arg[0])
elif sid_arg is not None and category_arg is not None and vtid_arg is not None:
	index.build_index(sid=sid_arg[0], category=category_arg[0], vtid=vtid_arg[0])
elif sid_arg is not None and category_arg is not None:
	index.build_index(sid=sid_arg[0], category=category_arg[0])
elif sid_arg is not None and eid_arg is not None:
	index.build_index(sid=sid_arg[0], eid=eid_arg[0])
elif sid_arg is not None:
	index.build_index(sid=sid_arg[0])
else:
	index.build_index()

