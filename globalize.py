#!/usr/bin/env python3

# reTux File Globalizer
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


import os
import shutil
import sys

import tkinter


if getattr(sys, "frozen", False):
    __file__ = sys.executable

FILEDIR = os.path.dirname(__file__)
CONFIG = os.path.join(os.path.expanduser("~"), ".config", "retux")


if __name__ == '__main__':
    if not os.path.exists(CONFIG):
        os.makedirs(CONFIG)

    tkwindow = tkinter.Tk()
    tkwindow.withdraw()
    fnames = tkinter.filedialog.askopenfilenames(
        filetypes=[("all files", ".*")], initialdir=CONFIG)
    for fname in fnames:
        rp = os.path.relpath(fname, CONFIG)
        if not rp.startswith(os.pardir):
            gd = os.path.dirname(os.path.join(FILEDIR, rp))
            if not os.path.exists(gd):
                os.makedirs(gd)

            new_name = os.path.join(gd, os.path.basename(fname))
            if os.path.isfile(new_name):
                os.remove(new_name)
            elif os.path.isdir(new_name):
                shutil.rmtree(new_name)

            shutil.move(fname, gd)
            tkinter.messagebox.showinfo(
                "Message", 'Moved "{}" to "{}"'.format(fname, gd))
        else:
            tkinter.messagebox.showinfo(
                "Message",
                '"{}" was not globalized (invalid location)'.format(fname))
    tkwindow.destroy()
