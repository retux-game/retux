#!/usr/bin/env python2

# Copyright (C) 2016 Julie Marchant <onpon4@riseup.net>
#
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

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import shutil

import six

CONFIG = os.path.join(os.path.expanduser("~"), ".config", "retux")


if __name__ == "__main__":
    try:
        shutil.copy(os.path.join(CONFIG, "stderr.txt"), os.getcwd())
    except IOError:
        print("No errors have been logged.")
        six.moves.input("Press Enter to exit.")
