# This file has been dedicated to the public domain, to the extent
# possible under applicable law, via CC0. See
# http://creativecommons.org/publicdomain/zero/1.0/ for more
# information. This file is offered as-is, without any warranty.

import os
import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
icon = None
if sys.platform == "win32":
    base = "Win32GUI"
    icon = os.path.join("data", "images", "misc", "icon.ico")

setup(name = "ReTux",
      version = "1.6.3",
      description = "Open source side-scrolling platformer starring Tux the penguin.",
      options = {"build_exe": build_exe_options},
      executables = [Executable("retux.py", base=base, icon=icon)])
