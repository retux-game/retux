# reTux
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

"""
Container module for global variables in ReTux.
"""


from lib import defs


fullscreen = False
scale_method = None
sound_enabled = True
music_enabled = True
stereo_enabled = True
fps_enabled = False
joystick_threshold = 0.1
left_key = [["left", "a"]]
right_key = [["right", "d"]]
up_key = [["up", "w"]]
down_key = [["down", "s"]]
jump_key = [["space"]]
action_key = [["ctrl_left", "ctrl_right"]]
sneak_key = [["shift_left", "shift_right"]]
menu_key = [["tab", "backspace"]]
pause_key = [["enter", "p"]]
left_js = [[(0, "axis-", 0), (0, "hat_left", 0)]]
right_js = [[(0, "axis+", 0), (0, "hat_right", 0)]]
up_js = [[(0, "axis-", 1), (0, "hat_up", 0)]]
down_js = [[(0, "axis+", 1), (0, "hat_down", 0)]]
jump_js = [[(0, "button", 1), (0, "button", 3)]]
action_js = [[(0, "button", 0)]]
sneak_js = [[(0, "button", 2)]]
menu_js = [[(0, "button", 8)]]
pause_js = [[(0, "button", 9)]]
save_slots = [None for i in range(defs.SAVE_NSLOTS)]

abort = False

current_save_slot = None
current_levelset = None
start_cutscene = None
worldmap = None
loaded_worldmaps = {}
levels = []
loaded_levels = {}
level_names = {}
level_timers = {}
cleared_levels = []
tuxdolls_available = []
tuxdolls_found = []
watched_timelines = []
level_time_bonus = 0
current_worldmap = None
worldmap_entry_space = None
current_worldmap_space = None
current_level = 0
current_checkpoints = {}

score = 0

current_areas = {}
main_area = None
level_cleared = False
mapdest = None
mapdest_space = None
