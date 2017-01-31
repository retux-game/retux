#!/usr/bin/env python2

# reTux
# Copyright (C) 2014-2017 onpon4 <onpon4@riseup.net>
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

__version__ = "1.3.4"

import argparse
import datetime
import gettext
import itertools
import json
import math
import os
import random
import shutil
import sys
import tempfile
import time
import traceback
import warnings
import weakref
import zipfile

import sge
import six
import tmx
import xsge_gui
import xsge_lighting
import xsge_path
import xsge_physics
import xsge_tmx

try:
    from six.moves.tkinter import Tk
    # six.moves.tkinter_filedialog doesn't work correctly.
    if six.PY2:
        import tkFileDialog as tkinter_filedialog
    else:
        import tkinter.filedialog as tkinter_filedialog
except ImportError:
    HAVE_TK = False
else:
    HAVE_TK = True


if getattr(sys, "frozen", False):
    __file__ = sys.executable

DATA = tempfile.mkdtemp("retux-data")
CONFIG = os.path.join(os.path.expanduser("~"), ".config", "retux")

dirs = [os.path.join(os.path.dirname(__file__), "data"),
        os.path.join(CONFIG, "data")]

if six.PY2:
    gettext.install("retux", os.path.abspath(os.path.join(dirs[0], "locale")),
                    unicode=True)
else:
    gettext.install("retux", os.path.abspath(os.path.join(dirs[0], "locale")))

parser = argparse.ArgumentParser()
parser.add_argument(
    "-p", "--print-errors",
    help=_("Print errors directly to stdout rather than saving them in a file."),
    action="store_true")
parser.add_argument(
    "-l", "--lang",
    help=_("Manually choose a different language to use."))
parser.add_argument(
    "--nodelta",
    help=_("Disable delta timing. Causes the game to slow down when it can't run at full speed instead of becoming choppier."),
    action="store_true")
parser.add_argument(
    "-d", "--datadir",
    help=_('Where to load the game data from (Default: "{}")').format(dirs[0]))
parser.add_argument(
    "--level",
    help=_("Play the indicated level and then exit."))
parser.add_argument(
    "--record",
    help=_("Start the indicated level and record player actions in a timeline. Useful for making cutscenes."))
parser.add_argument(
    "--no-backgrounds",
    help=_("Only show solid colors for backgrounds (uses less RAM)."),
    action="store_true")
parser.add_argument(
    "--no-hud", help=_("Don't show the player's heads-up display."),
    action="store_true")
parser.add_argument("--scale-basic", action="store_true")
parser.add_argument("--god")
args = parser.parse_args()

PRINT_ERRORS = args.print_errors
DELTA = not args.nodelta
if args.datadir:
    dirs[0] = args.datadir
LEVEL = args.level
RECORD = args.record
NO_BACKGROUNDS = args.no_backgrounds
NO_HUD = args.no_hud
GOD = (args.god and args.god.lower() == "plz4giv")

for d in dirs:
    if os.path.isdir(d):
        for dirpath, dirnames, filenames in os.walk(d, True, None, True):
            dirtail = os.path.relpath(dirpath, d)
            nd = os.path.join(DATA, dirtail)

            for dirname in dirnames:
                dp = os.path.join(nd, dirname)
                if not os.path.exists(dp):
                    os.makedirs(dp)

            for fname in filenames:
                shutil.copy2(os.path.join(dirpath, fname), nd)
del dirs

if six.PY2:
    gettext.install("retux", os.path.abspath(os.path.join(DATA, "locale")),
                    unicode=True)
else:
    gettext.install("retux", os.path.abspath(os.path.join(DATA, "locale")))

if args.lang:
    lang = gettext.translation("retux",
                               os.path.abspath(os.path.join(DATA, "locale")),
                               [args.lang])
    if six.PY2:
        lang.install(unicode=True)
    else:
        lang.install()

SCREEN_SIZE = [800, 448]
TILE_SIZE = 32
FPS = 56
DELTA_MIN = FPS / 2
DELTA_MAX = FPS * 4
TRANSITION_TIME = 750

DEFAULT_LEVELSET = "retux.json"
DEFAULT_LEVEL_TIME_BONUS = 90000

TUX_ORIGIN_X = 28
TUX_ORIGIN_Y = 16
TUX_KICK_TIME = 10

GRAVITY = 0.4

PLAYER_MAX_HP = 5
PLAYER_WALK_SPEED = 2
PLAYER_SKID_THRESHOLD = 3
PLAYER_RUN_SPEED = 4
PLAYER_MAX_SPEED = 5
PLAYER_ACCELERATION = 0.2
PLAYER_AIR_ACCELERATION = 0.1
PLAYER_FRICTION = 0.17
PLAYER_AIR_FRICTION = 0.03
PLAYER_JUMP_HEIGHT = 4 * TILE_SIZE + 2
PLAYER_RUN_JUMP_HEIGHT = 5 * TILE_SIZE + 2
PLAYER_STOMP_HEIGHT = TILE_SIZE / 2
PLAYER_FALL_SPEED = 8
PLAYER_SLIDE_ACCEL = 0.3
PLAYER_SLIDE_SPEED = 1
PLAYER_WALK_FRAMES_PER_PIXEL = 2 / 17
PLAYER_RUN_FRAMES_PER_PIXEL = 1 / 10
PLAYER_HITSTUN = 120
PLAYER_DIE_HEIGHT = 6 * TILE_SIZE
PLAYER_DIE_FALL_SPEED = 8

SNOWMAN_WALK_SPEED = 2
SNOWMAN_STRONG_WALK_SPEED = 3
SNOWMAN_FINAL_WALK_SPEED = 4
SNOWMAN_STUNNED_WALK_SPEED = 6
SNOWMAN_ACCELERATION = 0.1
SNOWMAN_STRONG_ACCELERATION = 0.2
SNOWMAN_FINAL_ACCELERATION = 0.5
SNOWMAN_HOP_HEIGHT = 2 * TILE_SIZE
SNOWMAN_JUMP_HEIGHT = 7 * TILE_SIZE
SNOWMAN_JUMP_TRIGGER = 2 * TILE_SIZE
SNOWMAN_STOMP_DELAY = 30
SNOWMAN_WALK_FRAMES_PER_PIXEL = 1 / 4
SNOWMAN_HP = 5
SNOWMAN_STRONG_STAGE = 2
SNOWMAN_FINAL_STAGE = 3
SNOWMAN_HITSTUN = 120
SNOWMAN_SHAKE_NUM = 3

RACCOT_WALK_SPEED = 3
RACCOT_ACCELERATION = 0.2
RACCOT_HOP_HEIGHT = TILE_SIZE
RACCOT_JUMP_HEIGHT = 5 * TILE_SIZE
RACCOT_JUMP_TRIGGER = 2 * TILE_SIZE
RACCOT_STOMP_SPEED = 4
RACCOT_STOMP_DELAY = 15
RACCOT_WALK_FRAMES_PER_PIXEL = 1 / 22
RACCOT_HP = 5
RACCOT_HOP_TIME = 5
RACCOT_HOP_INTERVAL_MIN = 45
RACCOT_HOP_INTERVAL_MAX = 120
RACCOT_CHARGE_INTERVAL_MIN = 300
RACCOT_CHARGE_INTERVAL_MAX = 600
RACCOT_CRUSH_LAX = -8 # A negative lax makes it have the opposite effect.
RACCOT_CRUSH_GRAVITY = 0.6
RACCOT_CRUSH_FALL_SPEED = 15
RACCOT_CRUSH_SPEED = 12
RACCOT_CRUSH_CHARGE = TILE_SIZE
RACCOT_SHAKE_NUM = 4

HP_POINTS = 1000
TIMER_FRAMES = 40
HEAL_COINS = 20

CEILING_LAX = 10
STOMP_LAX = 8

BLOCK_HIT_HEIGHT = 8
ITEM_HIT_HEIGHT = 16
COIN_COLLECT_TIME = 30
COIN_COLLECT_SPEED = 2
ITEM_SPAWN_SPEED = 1

SECOND_POINTS = 100
COIN_POINTS = 100
ENEMY_KILL_POINTS = 50
AMMO_POINTS = 10
TUXDOLL_POINTS = 5000

CAMERA_HSPEED_FACTOR = 1 / 2
CAMERA_VSPEED_FACTOR = 1 / 20
CAMERA_OFFSET_FACTOR = 10
CAMERA_MARGIN_TOP = 4 * TILE_SIZE
CAMERA_MARGIN_BOTTOM = 5 * TILE_SIZE
CAMERA_TARGET_MARGIN_BOTTOM = CAMERA_MARGIN_BOTTOM + TILE_SIZE

WARP_LAX = 12
WARP_SPEED = 1.5

SHAKE_FRAME_TIME = FPS / DELTA_MIN
SHAKE_AMOUNT = 3

ENEMY_WALK_SPEED = 1
ENEMY_FALL_SPEED = 7
ENEMY_SLIDE_SPEED = 0.3
ENEMY_HIT_BELOW_HEIGHT = TILE_SIZE * 3 / 4
SNOWBALL_BOUNCE_HEIGHT = TILE_SIZE * 3 + 2
KICK_FORWARD_SPEED = 6
KICK_FORWARD_HEIGHT = TILE_SIZE * 3 / 4
KICK_UP_HEIGHT = 5.5 * TILE_SIZE
ICEBLOCK_GRAVITY = 0.6
ICEBLOCK_FALL_SPEED = 9
ICEBLOCK_FRICTION = 0.1
ICEBLOCK_DASH_SPEED = 7
JUMPY_BOUNCE_HEIGHT = TILE_SIZE * 4
BOMB_GRAVITY = 0.6
BOMB_TICK_TIME = 4
EXPLOSION_TIME = FPS * 3 / 4
ICICLE_LAX = TILE_SIZE * 3 / 4
ICICLE_SHAKE_TIME = FPS
ICICLE_GRAVITY = 0.75
ICICLE_FALL_SPEED = 12
CRUSHER_LAX = TILE_SIZE * 3 / 4
CRUSHER_GRAVITY = 1
CRUSHER_FALL_SPEED = 15
CRUSHER_RISE_SPEED = 2
CRUSHER_CRUSH_TIME = FPS * 2 / 3
CRUSHER_SHAKE_NUM = 2
THAW_FPS = 15
THAW_TIME_DEFAULT = FPS * 5
THAW_WARN_TIME = FPS

BRICK_SHARD_NUM = 6
BRICK_SHARD_SPEED = 3
BRICK_SHARD_HEIGHT = TILE_SIZE * 2
BRICK_SHARD_GRAVITY = 0.75
BRICK_SHARD_FALL_SPEED = 12

ROCK_GRAVITY = 0.6
ROCK_FALL_SPEED = 10
ROCK_FRICTION = 0.4

SPRING_JUMP_HEIGHT = 8 * TILE_SIZE + 11

FLOWER_FALL_SPEED = 5
FLOWER_THROW_HEIGHT = TILE_SIZE / 2
FLOWER_THROW_UP_HEIGHT = TILE_SIZE * 3 / 2

FIREBALL_AMMO = 20
FIREBALL_SPEED = 8
FIREBALL_GRAVITY = 0.5
FIREBALL_FALL_SPEED = 5
FIREBALL_BOUNCE_HEIGHT = TILE_SIZE / 2
FIREBALL_UP_HEIGHT = TILE_SIZE * 3 / 2

ICEBULLET_AMMO = 20
ICEBULLET_SPEED = 16

COINBRICK_COINS = 20
COINBRICK_DECAY_TIME = 25

ICE_CRACK_TIME = 20
ICE_REFREEZE_RATE = 1 / 4

LIGHT_RANGE = 600

ACTIVATE_RANGE = 528
ENEMY_ACTIVE_RANGE = 32
ICEBLOCK_ACTIVE_RANGE = 400
BULLET_ACTIVE_RANGE = 96
ROCK_ACTIVE_RANGE = 464
TILE_ACTIVE_RANGE = 528
DEATHZONE = 2 * TILE_SIZE

DEATH_FADE_TIME = 3000
DEATH_RESTART_WAIT = FPS

WIN_COUNT_START_TIME = 120
WIN_COUNT_CONTINUE_TIME = 45
WIN_COUNT_POINTS_MULT = 111
WIN_COUNT_TIME_MULT = 311
WIN_FINISH_DELAY = 120

MAP_SPEED = 5

TEXT_SPEED = 1000

SAVE_NSLOTS = 10
MENU_MAX_ITEMS = 14

SOUND_MAX_RADIUS = 400
SOUND_ZERO_RADIUS = 1200
SOUND_CENTERED_RADIUS = 150
SOUND_TILTED_RADIUS = 1000
SOUND_TILT_LIMIT = 0.75

backgrounds = {}
loaded_music = {}
tux_grab_sprites = {}

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
save_slots = [None for i in six.moves.range(SAVE_NSLOTS)]

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


class Game(sge.dsp.Game):

    fps_time = 0
    fps_frames = 0
    fps_text = ""

    def event_step(self, time_passed, delta_mult):
        if fps_enabled:
            self.fps_time += time_passed
            self.fps_frames += 1
            if self.fps_time >= 250:
                self.fps_text = str(round(
                    (1000 * self.fps_frames) / self.fps_time, 2))
                self.fps_time = 0
                self.fps_frames = 0

            self.project_text(font_small, self.fps_text, self.width - 8,
                              self.height - 8, z=1000,
                              color=sge.gfx.Color("yellow"), halign="right",
                              valign="bottom")

    def event_mouse_button_press(self, button):
        if button == "middle":
            self.event_close()

    def event_close(self):
        rush_save()
        self.end()

    def event_paused_close(self):
        self.event_close()


class Level(sge.dsp.Room):

    """Handles levels."""

    def __init__(self, objects=(), width=None, height=None, views=None,
                 background=None, background_x=0, background_y=0,
                 object_area_width=TILE_SIZE * 2,
                 object_area_height=TILE_SIZE * 2,
                 name=None, bgname=None, music=None,
                 time_bonus=DEFAULT_LEVEL_TIME_BONUS, spawn=None,
                 timeline=None, ambient_light=None, disable_lights=False,
                 persistent=True):
        self.fname = None
        self.name = name
        self.music = music
        self.time_bonus = time_bonus
        self.spawn = spawn
        self.persistent = persistent
        self.points = 0
        self.timeline_objects = {}
        self.warps = []
        self.shake_queue = 0
        self.pause_delay = TRANSITION_TIME
        self.game_won = False
        self.status_text = None

        if bgname is not None:
            background = backgrounds.get(bgname, background)

        self.load_timeline(timeline)

        if ambient_light:
            self.ambient_light = sge.gfx.Color(ambient_light)
            if (self.ambient_light.red >= 255 and
                    self.ambient_light.green >= 255 and
                    self.ambient_light.blue >= 255):
                self.ambient_light = None
        else:
            self.ambient_light = None

        self.disable_lights = disable_lights or self.ambient_light is None

        super(Level, self).__init__(objects, width, height, views, background,
                                    background_x, background_y,
                                    object_area_width, object_area_height)
        self.add(gui_handler)

    def load_timeline(self, timeline):
        self.timeline = {}
        self.timeline_name = ""
        self.timeline_step = 0
        self.timeline_skip_target = None
        if timeline:
            self.timeline_name = timeline
            fname = os.path.join(DATA, "timelines", timeline)
            with open(fname, 'r') as f:
                jt = json.load(f)

            for i in jt:
                self.timeline[eval(i)] = jt[i]

    def add_timeline_object(self, obj):
        if obj.ID is not None:
            self.timeline_objects[obj.ID] = weakref.ref(obj)

    def timeline_skipto(self, step):
        t_keys = sorted(self.timeline.keys())
        self.timeline_step = step
        while t_keys and t_keys[0] < step:
            i = t_keys.pop(0)
            self.timeline[i] = []

    def add_points(self, x):
        if main_area not in cleared_levels:
            self.points += x

    def show_hud(self):
        # Show darkness
        if self.ambient_light:
            xsge_lighting.project_darkness(ambient_light=self.ambient_light,
                                           buffer=TILE_SIZE * 2)
        else:
            xsge_lighting.clear_lights()

        if not NO_HUD:
            if self.points:
                score_text = "{}+{}".format(score, self.points)
            else:
                score_text = str(score)
            time_bonus = level_timers.get(main_area, 0)
            text = "{}\n{}\n\n{}\n{}".format(
                _("Score"), score_text,
                _("Time Bonus") if time_bonus >= 0 else _("Time Penalty"),
                abs(time_bonus))
            sge.game.project_text(font, text, sge.game.width / 2, 0,
                                  color=sge.gfx.Color("white"),
                                  halign="center")

            if main_area in tuxdolls_available or main_area in tuxdolls_found:
                if main_area in tuxdolls_found:
                    s = tuxdoll_sprite
                else:
                    s = tuxdoll_transparent_sprite
                sge.game.project_sprite(s, 0, sge.game.width / 2, font.size * 6)

            if self.status_text:
                sge.game.project_text(font, self.status_text,
                                      sge.game.width / 2, sge.game.height - 16,
                                      color=sge.gfx.Color("white"),
                                      halign="center", valign="middle")
                self.status_text = None

    def shake(self, num=1):
        shaking = (self.shake_queue or "shake_up" in self.alarms or
                   "shake_down" in self.alarms)
        self.shake_queue = max(self.shake_queue, num)
        if not shaking:
            self.event_alarm("shake_down")

        for obj in self.objects:
            if isinstance(obj, SteadyIcicle):
                obj.check_shake(True)

    def pause(self):
        global level_timers
        global score

        if self.death_time is not None or "death" in self.alarms:
            if level_timers.setdefault(main_area, 0) >= 0:
                sge.snd.Music.stop()
                self.alarms["death"] = 0
        elif (self.timeline_skip_target is not None and
              self.timeline_step < self.timeline_skip_target):
            self.timeline_skipto(self.timeline_skip_target)
        elif self.pause_delay <= 0 and not self.won:
            sge.snd.Music.pause()
            play_sound(pause_sound)
            PauseMenu.create()

    def die(self):
        global current_areas
        current_areas = {}
        self.death_time = DEATH_FADE_TIME
        self.death_time_bonus = level_timers.setdefault(main_area, 0)
        if "timer" in self.alarms:
            del self.alarms["timer"]
        sge.snd.Music.clear_queue()
        sge.snd.Music.stop(DEATH_FADE_TIME)

    def return_to_map(self, completed=False):
        global current_worldmap
        global current_worldmap_space
        global mapdest
        global mapdest_space

        if completed:
            if mapdest:
                current_worldmap = mapdest
            if mapdest_space:
                current_worldmap_space = mapdest_space
                worldmap_entry_space = mapdest_space

        mapdest = None
        mapdest_space = None

        save_game()
        if current_worldmap:
            m = Worldmap.load(current_worldmap)
            m.start(transition="iris_out", transition_time=TRANSITION_TIME)
        else:
            sge.game.start_room.start()

    def win_level(self, victory_walk=True):
        global current_checkpoints

        for obj in self.objects[:]:
            if isinstance(obj, WinPuffObject) and obj.active:
                obj.win_puff()

        for obj in self.objects:
            if isinstance(obj, Player):
                obj.human = False
                obj.left_pressed = False
                obj.right_pressed = False
                obj.up_pressed = False
                obj.down_pressed = False
                obj.jump_pressed = False
                obj.action_pressed = False
                obj.sneak_pressed = True
                obj.jump_release()

                if victory_walk:
                    if obj.xvelocity >= 0:
                        obj.right_pressed = True
                    else:
                        obj.left_pressed = True

        if "timer" in self.alarms:
            del self.alarms["timer"]

        self.won = True
        self.alarms["win_count_points"] = WIN_COUNT_START_TIME
        current_checkpoints[main_area] = None
        sge.snd.Music.clear_queue()
        sge.snd.Music.stop()
        if music_enabled:
            level_win_music.play()

    def win_game(self):
        global current_level
        current_level = 0
        save_game()
        credits_room = CreditsScreen.load(os.path.join("special",
                                                       "credits.tmx"))
        credits_room.start()

    def event_room_start(self):
        self.add(coin_animation)
        self.add(bonus_animation)
        self.add(lava_animation)
        self.add(goal_animation)

        self.event_room_resume()

    def event_room_resume(self):
        global main_area
        global level_time_bonus

        xsge_lighting.clear_lights()

        self.won = False
        self.win_count_points = False
        self.win_count_time = False
        self.death_time = None
        self.alarms["timer"] = TIMER_FRAMES
        self.pause_delay = TRANSITION_TIME
        play_music(self.music)

        if main_area is None:
            main_area = self.fname

        if main_area == self.fname:
            level_time_bonus = self.time_bonus

        if GOD:
            level_timers[main_area] = min(0, level_timers.get(main_area, 0))
        elif main_area not in level_timers:
            if main_area in levels:
                level_timers[main_area] = level_time_bonus
            else:
                level_timers[main_area] = 0

        players = []
        spawn_point = None

        for obj in self.objects:
            if isinstance(obj, (Spawn, Door, WarpSpawn)):
                if self.spawn is not None and obj.spawn_id == self.spawn:
                    spawn_point = obj

                if isinstance(obj, Warp) and obj not in self.warps:
                    self.warps.append(obj)
            elif isinstance(obj, Player):
                players.append(obj)

        del_warps = []
        for warp in self.warps:
            if warp not in self.objects:
                del_warps.append(warp)
        for warp in del_warps:
            self.warps.remove(warp)

        if spawn_point is not None:
            for player in players:
                player.x = spawn_point.x
                player.y = spawn_point.y
                if player.view is not None:
                    player.view.x = player.x - player.view.width / 2
                    player.view.y = (player.y - player.view.height +
                                     CAMERA_TARGET_MARGIN_BOTTOM)

                if isinstance(spawn_point, WarpSpawn):
                    player.visible = False
                    player.tangible = False
                    player.warping = True
                    spawn_point.follow_start(player, WARP_SPEED)
                else:
                    player.visible = True
                    player.tangible = True
                    player.warping = False

    def event_step(self, time_passed, delta_mult):
        global watched_timelines
        global level_timers
        global current_level
        global score
        global current_areas
        global main_area
        global level_cleared

        if self.pause_delay > 0:
            self.pause_delay -= time_passed

        # Handle inactive objects and lighting
        if self.ambient_light:
            range_ = max(ACTIVATE_RANGE, LIGHT_RANGE)
        else:
            range_ = ACTIVATE_RANGE

        for view in self.views:
            for obj in self.get_objects_at(
                    view.x - range_, view.y - range_, view.width + range_ * 2,
                    view.height + range_ * 2):
                if isinstance(obj, InteractiveObject):
                    if not self.disable_lights:
                        obj.project_light()

                if not obj.active:
                    if isinstance(obj, InteractiveObject):
                        obj.update_active()
                    elif isinstance(obj, (Lava, LavaSurface)):
                        obj.image_index = lava_animation.image_index
                    elif isinstance(obj, (Goal, GoalTop)):
                        obj.image_index = goal_animation.image_index

        # Show HUD
        self.show_hud()

        # Timeline events
        t_keys = sorted(self.timeline.keys())
        while t_keys:
            i = t_keys.pop(0)
            if i <= self.timeline_step:
                while i in self.timeline and self.timeline[i]:
                    command = self.timeline[i].pop(0)
                    command = command.split(None, 1)
                    if command:
                        if len(command) >= 2:
                            command, arg = command[:2]
                        else:
                            command = command[0]
                            arg = ""

                        if command.startswith("#"):
                            # Comment; do nothing
                            pass
                        elif command == "setattr":
                            args = arg.split(None, 2)
                            if len(args) >= 3:
                                obj, name, value = args[:3]

                                try:
                                    value = eval(value)
                                except Exception as e:
                                    m = _("An error occurred in a timeline 'setattr' command:\n\n{}").format(
                                    traceback.format_exc())
                                    show_error(m)
                                else:
                                    if obj in self.timeline_objects:
                                        obj = self.timeline_objects[obj]()
                                        if obj is not None:
                                            setattr(obj, name, value)
                                    elif obj == "__level__":
                                        setattr(self, name, value)
                        elif command == "call":
                            args = arg.split()
                            if len(args) >= 2:
                                obj, method = args[:2]
                                fa = [eval(s) for s in args[2:]]

                                if obj in self.timeline_objects:
                                    obj = self.timeline_objects[obj]()
                                    if obj is not None:
                                        getattr(obj, method, lambda: None)(*fa)
                                elif obj == "__level__":
                                    getattr(self, method, lambda: None)(*fa)
                        elif command == "dialog":
                            args = arg.split(None, 1)
                            if len(args) >= 2:
                                portrait, text = args[:2]
                                sprite = portrait_sprites.get(portrait)
                                DialogBox(gui_handler, _(text), sprite).show()
                        elif command == "play_music":
                            self.music = arg
                            play_music(arg)
                        elif command == "timeline":
                            if self.timeline_name not in watched_timelines:
                                watched_timelines.append(self.timeline_name)
                            self.load_timeline(arg)
                            break
                        elif command == "skip_to":
                            try:
                                arg = float(arg)
                            except ValueError:
                                pass
                            else:
                                self.timeline_skipto(arg)
                                break
                        elif command == "exec":
                            try:
                                six.exec_(arg)
                            except Exception as e:
                                m = _("An error occurred in a timeline 'exec' command:\n\n{}").format(
                                    traceback.format_exc())
                                show_error(m)
                        elif command == "if":
                            try:
                                r = eval(arg)
                            except Exception as e:
                                m = _("An error occurred in a timeline 'if' statement:\n\n{}").format(
                                    traceback.format_exc())
                                show_error(m)
                                r = False
                            finally:
                                if not r:
                                    self.timeline[i] = []
                                    break
                        elif command == "if_watched":
                            if self.timeline_name not in watched_timelines:
                                self.timeline[i] = []
                                break
                        elif command == "if_not_watched":
                            if self.timeline_name in watched_timelines:
                                self.timeline[i] = []
                                break
                        elif command == "while":
                            try:
                                r = eval(arg)
                            except Exception as e:
                                m = _("An error occurred in a timeline 'while' statement:\n\n{}").format(
                                    traceback.format_exc())
                                show_error(m)
                                r = False
                            finally:
                                if r:
                                    cur_timeline = self.timeline[i][:]
                                    while_command = "while {}".format(arg)
                                    self.timeline[i].insert(0, while_command)
                                    t_keys.insert(0, i)
                                    self.timeline[i - 1] = cur_timeline
                                    self.timeline[i] = loop_timeline
                                    i -= 1
                                    self.timeline_step -= 1
                                else:
                                    self.timeline[i] = []
                                    break
                else:
                    del self.timeline[i]
            else:
                break
        else:
            if (self.timeline_name and
                    self.timeline_name not in watched_timelines):
                watched_timelines.append(self.timeline_name)
                self.timeline_name = ""

        self.timeline_step += delta_mult

        if self.death_time is not None:
            a = int(255 * (DEATH_FADE_TIME - self.death_time) / DEATH_FADE_TIME)
            sge.game.project_rectangle(
                0, 0, sge.game.width, sge.game.height, z=100,
                fill=sge.gfx.Color((0, 0, 0, min(a, 255))))

            time_bonus = level_timers.setdefault(main_area, 0)
            if time_bonus < 0 and cleared_levels:
                amt = int(math.copysign(
                    min(math.ceil(abs(self.death_time_bonus) * 3 * time_passed /
                                  DEATH_FADE_TIME),
                        abs(time_bonus)),
                    time_bonus))
                if amt:
                    score += amt
                    level_timers[main_area] -= amt
                    play_sound(coin_sound)

            if self.death_time < 0:
                self.death_time = None
                self.alarms["death"] = DEATH_RESTART_WAIT
            else:
                self.death_time -= time_passed
        elif "death" in self.alarms:
            sge.game.project_rectangle(0, 0, sge.game.width, sge.game.height,
                                       z=100, fill=sge.gfx.Color("black"))

        if self.won:
            if self.win_count_points:
                if self.points:
                    amt = int(math.copysign(
                        min(delta_mult * WIN_COUNT_POINTS_MULT,
                            abs(self.points)),
                        self.points))
                    score += amt
                    self.points -= amt
                    play_sound(coin_sound)
                else:
                    self.win_count_points = False
                    self.alarms["win_count_time"] = WIN_COUNT_CONTINUE_TIME
            elif self.win_count_time:
                time_bonus = level_timers.setdefault(main_area, 0)
                if time_bonus:
                    amt = int(math.copysign(
                        min(delta_mult * WIN_COUNT_TIME_MULT,
                            abs(time_bonus)),
                        time_bonus))
                    score += amt
                    level_timers[main_area] -= amt
                    play_sound(coin_sound)
                else:
                    self.win_count_time = False
                    if main_area not in cleared_levels:
                        self.alarms["win_count_hp"] = WIN_COUNT_CONTINUE_TIME
                    else:
                        self.alarms["win"] = WIN_FINISH_DELAY
            elif (not level_win_music.playing and
                  "win_count_points" not in self.alarms and
                  "win_count_time" not in self.alarms and
                  "win_count_hp" not in self.alarms and
                  "win" not in self.alarms):
                if main_area not in cleared_levels:
                    cleared_levels.append(main_area)

                current_areas = {}
                level_cleared = True

                if self.game_won:
                    self.win_game()
                elif current_worldmap:
                    self.return_to_map(True)
                else:
                    main_area = None
                    current_level += 1
                    if current_level < len(levels):
                        save_game()
                        level = self.__class__.load(levels[current_level],
                                                    True)
                        level.start(transition="fade")
                    else:
                        self.win_game()

    def event_paused_step(self, time_passed, delta_mult):
        # Handle lighting
        if self.ambient_light:
            range_ = max(ACTIVATE_RANGE, LIGHT_RANGE)
        else:
            range_ = ACTIVATE_RANGE

        for view in self.views:
            for obj in self.get_objects_at(
                    view.x - range_, view.y - range_, view.width + range_ * 2,
                    view.height + range_ * 2):
                if isinstance(obj, InteractiveObject):
                    if not self.disable_lights:
                        obj.project_light()

        self.show_hud()

    def event_alarm(self, alarm_id):
        global level_timers
        global score

        if alarm_id == "timer":
            if main_area in levels:
                level_timers.setdefault(main_area, 0)
                if main_area not in cleared_levels:
                    level_timers[main_area] -= SECOND_POINTS
                self.alarms["timer"] = TIMER_FRAMES
        elif alarm_id == "shake_down":
            self.shake_queue -= 1
            for view in self.views:
                view.yport += SHAKE_AMOUNT
            self.alarms["shake_up"] = SHAKE_FRAME_TIME
        elif alarm_id == "shake_up":
            for view in self.views:
                view.yport -= SHAKE_AMOUNT
            if self.shake_queue:
                self.alarms["shake_down"] = SHAKE_FRAME_TIME
        elif alarm_id == "death":
            # Project a black rectangle to prevent showing the level on
            # the last frame.
            sge.game.project_rectangle(0, 0, sge.game.width, sge.game.height,
                                       z=100, fill=sge.gfx.Color("black"))

            if (not cleared_levels and
                    current_checkpoints.get(main_area) is None):
                level_timers[main_area] = level_time_bonus

            if current_worldmap:
                self.return_to_map()
            elif main_area is not None:
                save_game()
                r = self.__class__.load(main_area, True)
                checkpoint = current_checkpoints.get(self.fname)
                if checkpoint is not None:
                    area_name, area_spawn = checkpoint.split(':', 1)
                    r = self.__class__.load(area_name, True)
                    r.spawn = area_spawn
                r.start()
        elif alarm_id == "win_count_points":
            if self.points > 0:
                self.win_count_points = True
            else:
                self.win_count_time = True
        elif alarm_id == "win_count_time":
            self.win_count_time = True
        elif alarm_id == "win_count_hp":
            if GOD:
                self.alarms["win"] = WIN_FINISH_DELAY
            else:
                for obj in self.objects:
                    if isinstance(obj, Player) and obj.hp > 0:
                        obj.hp -= 1
                        score += HP_POINTS
                        play_sound(heal_sound)
                        self.alarms["win_count_hp"] = WIN_COUNT_CONTINUE_TIME
                        break
                else:
                    self.alarms["win"] = WIN_FINISH_DELAY

    @classmethod
    def load(cls, fname, show_prompt=False):
        global level_names
        global tuxdolls_available

        if fname in current_areas:
            r = current_areas[fname]
        elif fname in loaded_levels:
            r = loaded_levels.pop(fname)
        else:
            if show_prompt:
                text = "Loading level..."
                if isinstance(sge.game.current_room, Worldmap):
                    sge.game.refresh()
                    sge.game.current_room.level_text = text
                    sge.game.current_room.event_step(0, 0)
                    sge.game.refresh()
                elif sge.game.current_room is not None:
                    x = sge.game.width / 2
                    y = sge.game.height / 2
                    w = font.get_width(text) + 32
                    h = font.get_height(text) + 32
                    sge.game.project_rectangle(x - w / 2, y - h / 2, w, h,
                                               fill=sge.gfx.Color("black"))
                    sge.game.project_text(font, text, x, y,
                                          color=sge.gfx.Color("white"),
                                          halign="center", valign="middle")
                    sge.game.refresh()
                else:
                    print(_("Loading \"{}\"...").format(fname))

            try:
                r = xsge_tmx.load(os.path.join(DATA, "levels", fname), cls=cls,
                                  types=TYPES)
            except Exception as e:
                m = _("An error occurred when trying to load the level:\n\n{}").format(
                    traceback.format_exc())
                show_error(m)
                r = None
            else:
                r.fname = fname

        if r is not None:
            if r.persistent:
                current_areas[fname] = r

            if fname not in level_names:
                name = r.name
                if name:
                    level_names[fname] = name
                elif fname in levels:
                    level_names[fname] = "Level {}".format(
                        levels.index(fname) + 1)
                else:
                    level_names[fname] = "???"

            if main_area in levels and main_area not in tuxdolls_available:
                for obj in r.objects:
                    if (isinstance(obj, TuxDoll) or
                            (isinstance(obj, (ItemBlock, HiddenItemBlock)) and
                             obj.item == "tuxdoll")):
                        tuxdolls_available.append(main_area)
                        break
            elif fname in levels and fname not in tuxdolls_available:
                for obj in r.objects:
                    if (isinstance(obj, TuxDoll) or
                            (isinstance(obj, (ItemBlock, HiddenItemBlock)) and
                             obj.item == "tuxdoll")):
                        tuxdolls_available.append(fname)
                        break

        return r


class LevelTester(Level):

    def return_to_map(self):
        sge.game.end()

    def win_game(self):
        sge.game.end()

    def event_alarm(self, alarm_id):
        if alarm_id == "death":
            sge.game.end()
        else:
            super(LevelTester, self).event_alarm(alarm_id)


class LevelRecorder(LevelTester):

    def __init__(self, *args, **kwargs):
        super(LevelRecorder, self).__init__(*args, **kwargs)
        self.recording = {}

    def add_recording_event(self, command):
        self.recording.setdefault(self.timeline_step, []).append(command)

    def event_key_press(self, key, char):
        if key == "f12":
            jt = self.recording

            fname = "recording_{}.json".format(time.time())
            with open(fname, 'w') as f:
                json.dump(jt, f, indent=4, sort_keys=True)

            sge.game.end()

        for i in self.timeline_objects:
            obj = self.timeline_objects[i]()
            if isinstance(obj, Player) and obj.human:
                if key in left_key[obj.player]:
                    self.add_recording_event(
                        "setattr {} left_pressed 1".format(obj.ID))
                if key in right_key[obj.player]:
                    self.add_recording_event(
                        "setattr {} right_pressed 1".format(obj.ID))
                if key in up_key[obj.player]:
                    self.add_recording_event("call {} press_up".format(obj.ID))
                    self.add_recording_event(
                        "setattr {} up_pressed 1".format(obj.ID))
                if key in down_key[obj.player]:
                    self.add_recording_event(
                        "setattr {} down_pressed 1".format(obj.ID))
                if key in jump_key[obj.player]:
                    self.add_recording_event("call {} jump".format(obj.ID))
                    self.add_recording_event(
                        "setattr {} jump_pressed 1".format(obj.ID))
                if key in action_key[obj.player]:
                    self.add_recording_event("call {} action".format(obj.ID))
                    self.add_recording_event(
                        "setattr {} action_pressed 1".format(obj.ID))
                if key in sneak_key[obj.player]:
                    self.add_recording_event(
                        "setattr {} sneak_pressed 1".format(obj.ID))

    def event_key_release(self, key):
        for i in self.timeline_objects:
            obj = self.timeline_objects[i]()
            if isinstance(obj, Player) and obj.human:
                if key in left_key[obj.player]:
                    self.add_recording_event(
                        "setattr {} left_pressed 0".format(obj.ID))
                if key in right_key[obj.player]:
                    self.add_recording_event(
                        "setattr {} right_pressed 0".format(obj.ID))
                if key in up_key[obj.player]:
                    self.add_recording_event(
                        "setattr {} up_pressed 0".format(obj.ID))
                if key in down_key[obj.player]:
                    self.add_recording_event(
                        "setattr {} down_pressed 0".format(obj.ID))
                if key in jump_key[obj.player]:
                    self.add_recording_event(
                        "call {} jump_release".format(obj.ID))
                    self.add_recording_event(
                        "setattr {} jump_pressed 0".format(obj.ID))
                if key in action_key[obj.player]:
                    self.add_recording_event(
                        "setattr {} action_pressed 0".format(obj.ID))
                if key in sneak_key[obj.player]:
                    self.add_recording_event(
                        "setattr {} sneak_pressed 0".format(obj.ID))


class SpecialScreen(Level):

    pass


class TitleScreen(SpecialScreen):

    def show_hud(self):
        pass

    def event_room_resume(self):
        super(TitleScreen, self).event_room_resume()
        MainMenu.create()

    def event_key_press(self, key, char):
        pass


class CreditsScreen(SpecialScreen):

    def event_room_start(self):
        super(CreditsScreen, self).event_room_start()

        if self.fname in current_areas:
            del current_areas[self.fname]

        if self.fname in loaded_levels:
            del loaded_levels[self.fname]

        with open(os.path.join(DATA, "credits.json"), 'r') as f:
            sections = json.load(f)

        logo_section = sge.dsp.Object.create(self.width / 2, self.height,
                                             sprite=logo_sprite,
                                             tangible=False)
        self.sections = [logo_section]
        for section in sections:
            if "title" in section:
                head_sprite = sge.gfx.Sprite.from_text(
                    font_big, section["title"], width=self.width,
                    color=sge.gfx.Color("white"), halign="center")
                x = self.width / 2
                y = self.sections[-1].bbox_bottom + font_big.size * 3
                head_section = sge.dsp.Object.create(x, y, sprite=head_sprite,
                                                     tangible=False)
                self.sections.append(head_section)

            if "lines" in section:
                for line in section["lines"]:
                    list_sprite = sge.gfx.Sprite.from_text(
                        font, line, width=self.width - 2 * TILE_SIZE,
                        color=sge.gfx.Color("white"), halign="center")
                    x = self.width / 2
                    y = self.sections[-1].bbox_bottom + font.size
                    list_section = sge.dsp.Object.create(
                        x, y, sprite=list_sprite, tangible=False)
                    self.sections.append(list_section)

        for obj in self.sections:
            obj.yvelocity = -0.5

    def event_step(self, time_passed, delta_mult):
        if self.sections[0].yvelocity > 0 and self.sections[0].y > self.height:
            for obj in self.sections:
                obj.yvelocity = 0

        if self.sections[-1].bbox_bottom < 0 and "end" not in self.alarms:
            sge.snd.Music.stop(fade_time=3000)
            self.alarms["end"] = 3.5 * FPS

    def event_alarm(self, alarm_id):
        if alarm_id == "end":
            sge.game.start_room.start()

    def event_key_press(self, key, char):
        if key in itertools.chain.from_iterable(down_key):
            if "end" not in self.alarms:
                for obj in self.sections:
                    obj.yvelocity -= 0.25
        elif key in itertools.chain.from_iterable(up_key):
            if "end" not in self.alarms:
                for obj in self.sections:
                    obj.yvelocity += 0.25
        elif (key in itertools.chain.from_iterable(jump_key) or
                key in itertools.chain.from_iterable(action_key) or
                key in itertools.chain.from_iterable(pause_key)):
            sge.game.start_room.start()

    def event_joystick(self, js_name, js_id, input_type, input_id, value):
        js = (js_id, input_type, input_id)
        if value >= joystick_threshold:
            if js in itertools.chain.from_iterable(down_js):
                if "end" not in self.alarms:
                    for obj in self.sections:
                        obj.yvelocity -= 0.25
            elif js in itertools.chain.from_iterable(up_js):
                if "end" not in self.alarms:
                    for obj in self.sections:
                        obj.yvelocity += 0.25
            elif (js in itertools.chain.from_iterable(jump_js) or
                    js in itertools.chain.from_iterable(action_js) or
                    js in itertools.chain.from_iterable(pause_js)):
                sge.game.start_room.start()


class Worldmap(sge.dsp.Room):

    """Handles worldmaps."""

    def __init__(self, objects=(), width=None, height=None, views=None,
                 background=None, background_x=0, background_y=0,
                 object_area_width=TILE_SIZE * 2,
                 object_area_height=TILE_SIZE * 2, music=None):
        self.music = music
        super(Worldmap, self).__init__(objects, width, height, views,
                                       background, background_x, background_y,
                                       object_area_width, object_area_height)

    def show_menu(self):
        sge.snd.Music.pause()
        play_sound(pause_sound)
        WorldmapMenu.create()

    def event_room_start(self):
        self.level_text = None
        self.level_tuxdoll_available = False
        self.level_tuxdoll_found = False
        self.event_room_resume()

    def event_room_resume(self):
        global loaded_levels
        global main_area
        global current_areas
        global level_cleared

        main_area = None

        for obj in self.objects:
            if isinstance(obj, MapSpace):
                obj.update_sprite()

        play_music(self.music)
        level_cleared = False

    def event_step(self, time_passed, delta_mult):
        text = " {}/{}".format(len(tuxdolls_found), len(tuxdolls_available))
        w = tuxdoll_sprite.width + font.get_width(text)

        x = sge.game.width / 2 + tuxdoll_sprite.origin_x - w / 2
        y = tuxdoll_sprite.origin_y + 16
        sge.game.project_sprite(tuxdoll_shadow_sprite, 0, x + 2, y + 2)
        sge.game.project_sprite(tuxdoll_sprite, 0, x, y)

        x += tuxdoll_sprite.width - tuxdoll_sprite.origin_x
        sge.game.project_text(font, text, x + 2, y + 2,
                              color=sge.gfx.Color("black"), halign="left",
                              valign="middle")
        sge.game.project_text(font, text, x, y, color=sge.gfx.Color("white"),
                              halign="left", valign="middle")

        if self.level_text:
            x = sge.game.width / 2
            y = sge.game.height - font.size
            sge.game.project_text(font, self.level_text, x + 2, y + 2,
                                  color=sge.gfx.Color("black"),
                                  halign="center", valign="bottom")
            sge.game.project_text(font, self.level_text, x, y,
                                  color=sge.gfx.Color("white"),
                                  halign="center", valign="bottom")

        if self.level_tuxdoll_available:
            x = sge.game.width / 2
            y = sge.game.height - font.size * 4
            if self.level_tuxdoll_found:
                sge.game.project_sprite(tuxdoll_shadow_sprite, 0, x + 2, y + 2)
                sge.game.project_sprite(tuxdoll_sprite, 0, x, y)
            else:
                sge.game.project_sprite(tuxdoll_transparent_sprite, 0, x, y)

    @classmethod
    def load(cls, fname):
        if fname in loaded_worldmaps:
            return loaded_worldmaps.pop(fname)
        else:
            return xsge_tmx.load(os.path.join(DATA, "worldmaps", fname),
                                 cls=cls, types=TYPES)


class SolidLeft(xsge_physics.SolidLeft):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SolidLeft, self).__init__(*args, **kwargs)


class SolidRight(xsge_physics.SolidRight):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SolidRight, self).__init__(*args, **kwargs)


class SolidTop(xsge_physics.SolidTop):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SolidTop, self).__init__(*args, **kwargs)


class SolidBottom(xsge_physics.SolidBottom):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SolidBottom, self).__init__(*args, **kwargs)


class Solid(xsge_physics.Solid):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(Solid, self).__init__(*args, **kwargs)


class SlopeTopLeft(xsge_physics.SlopeTopLeft):

    xsticky_top = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SlopeTopLeft, self).__init__(*args, **kwargs)


class SlopeTopRight(xsge_physics.SlopeTopRight):

    xsticky_top = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SlopeTopRight, self).__init__(*args, **kwargs)


class SlopeBottomLeft(xsge_physics.SlopeBottomLeft):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SlopeBottomLeft, self).__init__(*args, **kwargs)


class SlopeBottomRight(xsge_physics.SlopeBottomRight):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SlopeBottomRight, self).__init__(*args, **kwargs)


class MovingPlatform(xsge_physics.SolidTop, xsge_physics.MobileWall):

    sticky_top = True

    def __init__(self, x, y, z=0, **kwargs):
        kwargs.setdefault("sprite", platform_sprite)
        super(MovingPlatform, self).__init__(x, y, z, **kwargs)
        self.path = None
        self.following = False

    def event_step(self, time_passed, delta_mult):
        super(MovingPlatform, self).event_step(time_passed, delta_mult)

        if self.path and not self.following:
            for other in self.collision(Player, y=(self.y - 1)):
                if self in other.get_bottom_touching_wall():
                    self.path.follow_start(self, self.path.path_speed,
                                           accel=self.path.path_accel,
                                           decel=self.path.path_decel,
                                           loop=self.path.path_loop)
                    break


class HurtLeft(SolidLeft):

    pass


class HurtRight(SolidRight):

    pass


class HurtTop(SolidTop):

    pass


class HurtBottom(SolidBottom):

    pass


class SpikeLeft(HurtLeft, xsge_physics.Solid):

    pass


class SpikeRight(HurtRight, xsge_physics.Solid):

    pass


class SpikeTop(HurtTop, xsge_physics.Solid):

    pass


class SpikeBottom(HurtBottom, xsge_physics.Solid):

    pass


class Death(sge.dsp.Object):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(Death, self).__init__(*args, **kwargs)


class LevelEnd(sge.dsp.Object):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(LevelEnd, self).__init__(*args, **kwargs)


class Player(xsge_physics.Collider):

    name = "Tux"
    max_hp = PLAYER_MAX_HP
    walk_speed = PLAYER_WALK_SPEED
    run_speed = PLAYER_RUN_SPEED
    max_speed = PLAYER_MAX_SPEED
    acceleration = PLAYER_ACCELERATION
    air_acceleration = PLAYER_AIR_ACCELERATION
    friction = PLAYER_FRICTION
    air_friction = PLAYER_AIR_FRICTION
    jump_height = PLAYER_JUMP_HEIGHT
    run_jump_height = PLAYER_RUN_JUMP_HEIGHT
    stomp_height = PLAYER_STOMP_HEIGHT
    gravity = GRAVITY
    fall_speed = PLAYER_FALL_SPEED
    slide_accel = PLAYER_SLIDE_ACCEL
    slide_speed = PLAYER_SLIDE_SPEED
    hitstun_time = PLAYER_HITSTUN
    carry_x = 0
    carry_y = 20

    @property
    def warping(self):
        return self.__warping

    @warping.setter
    def warping(self, value):
        self.__warping = value
        if self.held_object is not None:
            if value:
                self.held_object.x = -666
                self.held_object.y = -666 * (self.player + 1)
            else:
                self.held_object.x = self.x + self.held_object.image_origin_x
                self.held_object.y = self.y
                if self.image_xscale < 0:
                    self.held_object.x -= self.held_object.sprite.width

    def __init__(self, x, y, z=0, sprite=None, visible=True, active=True,
                 checks_collisions=True, tangible=True, bbox_x=-13, bbox_y=2,
                 bbox_width=26, bbox_height=30, regulate_origin=True,
                 collision_ellipse=False, collision_precise=False, xvelocity=0,
                 yvelocity=0, xacceleration=0, yacceleration=0,
                 xdeceleration=0, ydeceleration=0, image_index=0,
                 image_origin_x=None, image_origin_y=None, image_fps=None,
                 image_xscale=1, image_yscale=1, image_rotation=0,
                 image_alpha=255, image_blend=None, ID="player", player=0,
                 human=True, lose_on_death=True, view_frozen=False,
                 view_is_barrier=True):
        self.ID = ID
        self.player = player
        self.human = human
        self.lose_on_death = lose_on_death
        self.view_frozen = view_frozen
        self.view_is_barrier = view_is_barrier

        self.held_object = None
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.jump_pressed = False
        self.action_pressed = False
        self.sneak_pressed = False
        self.hp = self.max_hp
        self.coins = 0
        self.hitstun = False
        self.warping = False
        self.facing = 1
        self.view = None

        if GOD:
            image_blend = sge.gfx.Color("yellow")

        super(Player, self).__init__(
            x, y, z=z, sprite=sprite, visible=visible, active=active,
            checks_collisions=checks_collisions, tangible=tangible,
            bbox_x=bbox_x, bbox_y=bbox_y, bbox_width=bbox_width,
            bbox_height=bbox_height, regulate_origin=regulate_origin,
            collision_ellipse=collision_ellipse,
            collision_precise=collision_precise, xvelocity=xvelocity,
            yvelocity=yvelocity, xacceleration=xacceleration,
            yacceleration=yacceleration, xdeceleration=xdeceleration,
            ydeceleration=ydeceleration, image_index=image_index,
            image_origin_x=image_origin_x, image_origin_y=image_origin_y,
            image_fps=image_fps, image_xscale=image_xscale,
            image_yscale=image_yscale, image_rotation=image_rotation,
            image_alpha=image_alpha, image_blend=image_blend)

    def refresh_input(self):
        if self.human:
            key_controls = [left_key, right_key, up_key, down_key, jump_key,
                            action_key, sneak_key]
            js_controls = [left_js, right_js, up_js, down_js, jump_js,
                           action_js, sneak_js]
            states = [0 for i in key_controls]

            for i in six.moves.range(len(key_controls)):
                for choice in key_controls[i][self.player]:
                    value = sge.keyboard.get_pressed(choice)
                    states[i] = max(states[i], value)

            for i in six.moves.range(len(js_controls)):
                for choice in js_controls[i][self.player]:
                    j, t, c = choice
                    value = min(sge.joystick.get_value(j, t, c), 1)
                    if value >= joystick_threshold:
                        states[i] = max(states[i], value)

            self.left_pressed = states[0]
            self.right_pressed = states[1]
            self.up_pressed = states[2]
            self.down_pressed = states[3]
            self.jump_pressed = states[4]
            self.action_pressed = states[5]
            self.sneak_pressed = states[6]

    def jump(self):
        if not self.warping and (self.on_floor or self.was_on_floor):
            for thin_ice in self.collision(ThinIce, y=(self.y + 1)):
                thin_ice.crack()
                thin_ice.crack()

            if abs(self.xvelocity) >= self.run_speed:
                self.yvelocity = get_jump_speed(self.run_jump_height,
                                                self.gravity)
            else:
                self.yvelocity = get_jump_speed(self.jump_height, self.gravity)
            self.on_floor = []
            self.was_on_floor = []
            play_sound(jump_sound, self.x, self.y)

    def jump_release(self):
        if self.yvelocity < 0:
            self.yvelocity /= 2

    def action(self):
        if not self.warping and self.held_object is not None:
            if self.up_pressed:
                self.held_object.kick_up()
            elif self.down_pressed:
                self.held_object.drop()
            else:
                self.held_object.kick()

    def press_up(self):
        if self.on_floor and self.was_on_floor:
            for door in sorted(self.collision(Door),
                               key=lambda o, x=self.x: -abs(x - o.x)):
                if self.y == door.y and abs(self.x - door.x) <= WARP_LAX:
                    self.move_x(door.x - self.x)
                    if abs(self.x - door.x) < 1:
                        self.x = door.x
                        door.warp(self)
                        break

    def stomp_jump(self, other, jump_height=None):
        if jump_height is None:
            jump_height = self.jump_height

        if self.jump_pressed:
            self.yvelocity = get_jump_speed(jump_height, self.gravity)
        else:
            self.yvelocity = get_jump_speed(self.stomp_height, self.gravity)
        T = math.floor(other.bbox_top / TILE_SIZE) * TILE_SIZE
        self.move_y(T - self.bbox_bottom)

    def hurt(self):
        if not GOD and not self.hitstun and not sge.game.current_room.won:
            self.hp -= 1
            if self.hp <= 0:
                self.kill()
            else:
                play_sound(hurt_sound, self.x, self.y)
                self.hitstun = True
                self.image_alpha = 128
                self.alarms["hitstun"] = self.hitstun_time

    def kill(self, show_fall=True):
        if GOD:
            self.yvelocity = get_jump_speed(SCREEN_SIZE[1], self.gravity)
            play_sound(hurt_sound, self.x, self.y)
        else:
            if self.held_object is not None:
                self.held_object.drop()
            play_sound(kill_sound, self.x, self.y)
            if show_fall:
                DeadMan.create(self.x, self.y, 100000, sprite=tux_die_sprite,
                               yvelocity=get_jump_speed(PLAYER_DIE_HEIGHT))

            if self.lose_on_death and not sge.game.current_room.won:
                sge.game.current_room.die()

            self.destroy()

    def pickup(self, other):
        if self.held_object is None and other.parent is None:
            other.visible = False
            self.held_object = other
            other.parent = self
            return True
        else:
            return False

    def drop_object(self):
        if self.held_object is not None:
            self.held_object.visible = True
            self.held_object = None

    def do_kick(self):
        play_sound(kick_sound, self.x, self.y)
        self.alarms["fixed_sprite"] = TUX_KICK_TIME
        if self.held_object is not None:
            self.sprite = self.get_grab_sprite(tux_body_kick_sprite)
        else:
            self.sprite = tux_kick_sprite

    def kick_object(self):
        self.drop_object()
        self.do_kick()

    def show_hud(self):
        if not NO_HUD:
            y = 0
            sge.game.project_text(font, self.name, 0, y,
                                  color=sge.gfx.Color("white"))

            x = 0
            y += 36
            for i in six.moves.range(self.max_hp):
                if self.hp >= i + 1:
                    sge.game.project_sprite(heart_full_sprite, 0, x, y)
                else:
                    sge.game.project_sprite(heart_empty_sprite, 0, x, y)
                x += heart_empty_sprite.width

            y += 18
            sge.game.project_sprite(coin_icon_sprite,
                                    coin_animation.image_index, 0, y)
            sge.game.project_text(font, "x{}".format(self.coins), 16, y,
                                  color=sge.gfx.Color("white"))

            if not self.human:
                room = sge.game.current_room
                if (room.timeline_skip_target is not None and
                        room.timeline_step < room.timeline_skip_target):
                    room.status_text = _("Press the Menu button to skip...")
                else:
                    room.status_text = _("Cinematic mode enabled")

    def get_grab_sprite(self, body_sprite, arms_sprite=None):
        if arms_sprite is None: arms_sprite = tux_arms_grab_sprite

        if self.held_object is not None:
            obj_sprite = self.held_object.sprite
            obj_image_index = self.held_object.image_index
            obj_image_xscale = self.held_object.image_xscale
            obj_image_yscale = self.held_object.image_yscale

            i = (id(body_sprite), id(obj_sprite), obj_image_index,
                 obj_image_xscale, obj_image_yscale)
            if i in tux_grab_sprites:
                return tux_grab_sprites[i]
            else:
                if abs(obj_image_xscale) != 1 or abs(obj_image_yscale) != 1:
                    obj_sprite = obj_sprite.copy()
                    obj_sprite.width *= abs(obj_image_xscale)
                    obj_sprite.height *= abs(obj_image_yscale)

                origin_x = body_sprite.origin_x
                origin_y = body_sprite.origin_y
                width = body_sprite.width
                height = body_sprite.height

                left = body_sprite.origin_x + self.carry_x
                if left < 0:
                    origin_x -= left
                    width -= left
                width = max(width, left + obj_sprite.width)

                top = (body_sprite.origin_y + self.carry_y -
                       obj_sprite.origin_y - obj_sprite.height)
                if top < 0:
                    origin_y -= top
                    height -= top
                height = max(height, top + obj_sprite.height)

                grab_sprite = sge.gfx.Sprite(
                    width=width, height=height, origin_x=origin_x,
                    origin_y=origin_y)
                for j in six.moves.range(1, body_sprite.frames):
                    grab_sprite.append_frame()
                grab_sprite.draw_lock()
                for j in six.moves.range(grab_sprite.frames):
                    x = origin_x + obj_sprite.origin_x
                    y = (origin_y + self.carry_y + obj_sprite.origin_y -
                         obj_sprite.height)
                    grab_sprite.draw_sprite(obj_sprite, obj_image_index, x, y,
                                            j)
                    grab_sprite.draw_sprite(body_sprite, j, origin_x, origin_y,
                                            j)
                    grab_sprite.draw_sprite(arms_sprite, j, origin_x, origin_y,
                                            j)
                grab_sprite.draw_unlock()
                tux_grab_sprites[i] = grab_sprite
                return grab_sprite
        else:
            i = id(body_sprite)
            if i in tux_grab_sprites:
                return tux_grab_sprites[i]
            else:
                grab_sprite = body_sprite.copy()
                grab_sprite.draw_lock()
                for j in six.moves.range(grab_sprite.frames):
                    grab_sprite.draw_sprite(arms_sprite, j,
                                            grab_sprite.origin_x,
                                            grab_sprite.origin_y, j)
                grab_sprite.draw_unlock()
                tux_grab_sprites[i] = grab_sprite
                return grab_sprite

    def set_image(self):
        h_control = bool(self.right_pressed) - bool(self.left_pressed)
        hands_free = (self.held_object is None)

        if self.on_floor and self.was_on_floor:
            xm = (self.xvelocity > 0) - (self.xvelocity < 0)
            speed = abs(self.xvelocity)
            if speed > 0:
                if xm != self.facing:
                    skidding = skid_sound.playing
                    if (not skidding and h_control and
                            speed >= PLAYER_SKID_THRESHOLD):
                        skidding = True
                        play_sound(skid_sound, self.x, self.y)
                else:
                    skidding = False

                if skidding:
                    if hands_free:
                        self.sprite = tux_skid_sprite
                    else:
                        self.sprite = self.get_grab_sprite(
                            tux_body_skid_sprite, tux_arms_skid_grab_sprite)
                else:
                    if (xm != self.facing or
                            abs(self.xvelocity) < self.run_speed):
                        if hands_free:
                            self.sprite = tux_walk_sprite
                        else:
                            self.sprite = self.get_grab_sprite(
                                tux_body_walk_sprite)

                        self.image_speed = speed * PLAYER_WALK_FRAMES_PER_PIXEL
                        if xm != self.facing:
                            self.image_speed *= -1
                    else:
                        if hands_free:
                            self.sprite = tux_run_sprite
                        else:
                            self.sprite = self.get_grab_sprite(
                                tux_body_run_sprite)

                        self.image_speed = speed * PLAYER_RUN_FRAMES_PER_PIXEL
            else:
                if hands_free:
                    self.sprite = tux_stand_sprite
                else:
                    self.sprite = self.get_grab_sprite(
                        tux_body_stand_sprite)
        else:
            if self.yvelocity < 0:
                if hands_free:
                    self.sprite = tux_jump_sprite
                else:
                    self.sprite = self.get_grab_sprite(tux_body_jump_sprite)
            else:
                if hands_free:
                    self.sprite = tux_fall_sprite
                else:
                    self.sprite = self.get_grab_sprite(tux_body_fall_sprite)

    def set_warp_image(self):
        hands_free = (self.held_object is None)

        if abs(self.xvelocity) >= WARP_SPEED / 2:
            if hands_free:
                self.sprite = tux_walk_sprite
            else:
                self.sprite = self.get_grab_sprite(tux_body_walk_sprite)

            self.image_speed = WARP_SPEED * PLAYER_WALK_FRAMES_PER_PIXEL
            if self.xvelocity > 0:
                self.image_xscale = abs(self.image_xscale)
            else:
                self.image_xscale = -abs(self.image_xscale)
        else:
            if self.on_floor and self.was_on_floor and abs(self.yvelocity) < 1:
                if hands_free:
                    self.sprite = tux_stand_sprite
                else:
                    self.sprite = self.get_grab_sprite(tux_body_stand_sprite)
            else:
                if hands_free:
                    self.sprite = tux_jump_sprite
                else:
                    self.sprite = self.get_grab_sprite(tux_body_jump_sprite)

    def event_create(self):
        sge.game.current_room.add_timeline_object(self)

        self.last_x = self.x
        self.last_y = self.y
        self.on_slope = self.get_bottom_touching_slope()
        self.on_floor = self.get_bottom_touching_wall() + self.on_slope
        self.was_on_floor = self.on_floor

        self.view = sge.game.current_room.views[self.player]
        self.view.x = self.x - self.view.width / 2
        self.view.y = self.y - self.view.height + CAMERA_TARGET_MARGIN_BOTTOM

    def event_update_position(self, delta_mult):
        super(Player, self).event_update_position(delta_mult)

        held_object = self.held_object
        if not self.warping and held_object is not None:
            target_x = self.x + held_object.sprite.origin_x + self.carry_x
            h = held_object.sprite.height * abs(held_object.image_yscale)
            target_y = self.y + held_object.sprite.origin_y - h + self.carry_y
            if self.image_xscale < 0:
                target_x -= (held_object.sprite.width *
                             abs(held_object.image_xscale))
                target_x -= 2 * self.carry_x
            if isinstance(held_object, xsge_physics.Collider):
                held_object.move_x(target_x - held_object.x)
                held_object.move_y(target_y - held_object.y)
            else:
                held_object.x = target_x
                held_object.y = target_y

            held_object.image_xscale = math.copysign(held_object.image_xscale,
                                                     self.image_xscale)
            held_object.image_yscale = math.copysign(held_object.image_yscale,
                                                     self.image_yscale)

    def event_begin_step(self, time_passed, delta_mult):
        if not self.warping:
            self.refresh_input()

            h_control = bool(self.right_pressed) - bool(self.left_pressed)
            current_h_movement = (self.xvelocity > 0) - (self.xvelocity < 0)

            self.xacceleration = 0
            self.yacceleration = 0
            self.xdeceleration = 0

            if abs(self.xvelocity) >= self.max_speed:
                self.xvelocity = self.max_speed * current_h_movement

            if h_control:
                self.facing = h_control
                self.image_xscale = h_control * abs(self.image_xscale)
                h_factor = abs(self.right_pressed - self.left_pressed)
                target_speed = min(h_factor * self.max_speed, self.max_speed)
                if self.sneak_pressed:
                    target_speed = min(target_speed, self.walk_speed)
                if (abs(self.xvelocity) < target_speed or
                        h_control != current_h_movement):
                    if self.on_floor or self.was_on_floor:
                        self.xacceleration = self.acceleration * h_control
                    else:
                        self.xacceleration = self.air_acceleration * h_control
                else:
                    if self.on_floor or self.was_on_floor:
                        dc = self.friction
                    else:
                        dc = self.air_friction

                    if abs(self.xvelocity) - dc * delta_mult > target_speed:
                        self.xdeceleration = dc
                    else:
                        self.xvelocity = target_speed * current_h_movement

            if current_h_movement and h_control != current_h_movement:
                if self.on_floor or self.was_on_floor:
                    self.xdeceleration = self.friction
                else:
                    self.xdeceleration = self.air_friction

            if not self.on_floor and not self.was_on_floor:
                if self.yvelocity < self.fall_speed:
                    self.yacceleration = self.gravity
                else:
                    self.yvelocity = self.fall_speed
            elif self.on_slope:
                self.yvelocity = (self.slide_speed *
                                  (self.on_slope[0].bbox_height /
                                   self.on_slope[0].bbox_width))

    def event_step(self, time_passed, delta_mult):
        if self.warping:
            self.event_step_warp(time_passed, delta_mult)
        else:
            self.event_step_normal(time_passed, delta_mult)

        # Move view
        if not self.view_frozen:
            view_target_x = (self.x - self.view.width / 2 +
                             self.xvelocity * CAMERA_OFFSET_FACTOR)
            if abs(view_target_x - self.view.x) > 0.5:
                self.view.x += ((view_target_x - self.view.x) *
                                CAMERA_HSPEED_FACTOR)
            else:
                self.view.x = view_target_x

            view_min_y = self.y - self.view.height + CAMERA_MARGIN_BOTTOM
            view_max_y = self.y - CAMERA_MARGIN_TOP

            if self.warping or (self.on_floor and self.was_on_floor):
                view_target_y = (self.y - self.view.height +
                                 CAMERA_TARGET_MARGIN_BOTTOM)
                if abs(view_target_y - self.view.y) > 0.5:
                    self.view.y += ((view_target_y - self.view.y) *
                                    CAMERA_VSPEED_FACTOR)
                else:
                    self.view.y = view_target_y

            if self.view.y < view_min_y:
                self.view.y = view_min_y
            elif self.view.y > view_max_y:
                self.view.y = view_max_y

        self.last_x = self.x
        self.last_y = self.y

        if self.bbox_bottom <= self.view.y:
            sge.game.current_room.project_sprite(tux_offscreen_sprite, 0,
                                                 self.x, 0, self.z)

        while self.coins >= HEAL_COINS:
            self.coins -= HEAL_COINS
            play_sound(heal_sound)
            if self.hp < self.max_hp:
                self.hp += 1
            else:
                sge.game.current_room.add_points(HP_POINTS)

        self.show_hud()

    def event_step_normal(self, time_passed, delta_mult):
        on_floor = self.get_bottom_touching_wall()
        self.on_slope = self.get_bottom_touching_slope() if not on_floor else []
        self.was_on_floor = self.on_floor
        self.on_floor = on_floor + self.on_slope
        h_control = bool(self.right_pressed) - bool(self.left_pressed)
        v_control = bool(self.down_pressed) - bool(self.up_pressed)

        for block in self.on_floor:
            if block in self.was_on_floor and isinstance(block, HurtTop):
                self.hurt()

        # Set image
        if "fixed_sprite" not in self.alarms:
            self.set_image()

        # Enter warp pipes
        if h_control > 0 and self.xvelocity >= 0:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "right" and self.bbox_right == warp.x and
                        abs(self.y - warp.y) < WARP_LAX):
                    self.y = warp.y
                    warp.warp(self)
        elif h_control < 0 and self.xvelocity <= 0:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "left" and self.bbox_left == warp.x and
                        abs(self.y - warp.y) < WARP_LAX):
                    self.y = warp.y
                    warp.warp(self)

        if v_control > 0 and self.yvelocity >= 0:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "down" and self.bbox_bottom == warp.y and
                        abs(self.x - warp.x) < WARP_LAX):
                    self.x = warp.x
                    warp.warp(self)
        elif v_control < 0 and self.yvelocity <= 0:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "up" and self.bbox_top == warp.y and
                        abs(self.x - warp.x) < WARP_LAX):
                    self.x = warp.x
                    warp.warp(self)

        # Prevent moving off-screen to the right or left
        if self.view_is_barrier:
            if self.bbox_left < self.view.x:
                self.move_x(self.view.x - self.bbox_left, True)
                self.bbox_left = self.view.x
            elif self.bbox_right > self.view.x + self.view.width:
                self.move_x(self.view.x + self.view.width - self.bbox_right,
                            True)
                self.bbox_right = self.view.x + self.view.width

        # Off-screen death
        if (not sge.game.current_room.won and
                self.bbox_top > self.view.y + self.view.height + DEATHZONE):
            self.kill(False)

    def event_step_warp(self, time_passed, delta_mult):
        self.set_warp_image()

    def event_paused_step(self, time_passed, delta_mult):
        self.show_hud()

    def event_alarm(self, alarm_id):
        if alarm_id == "hitstun":
            self.hitstun = False
            self.image_alpha = 255

    def event_key_press(self, key, char):
        if self.human:
            if key in jump_key[self.player]:
                self.jump()
            if key in action_key[self.player]:
                self.action()
            if key in up_key[self.player]:
                self.press_up()

        if not isinstance(sge.game.current_room, SpecialScreen):
            if (key == "escape" or key in pause_key[self.player] or
                    key in menu_key[self.player]):
                sge.game.current_room.pause()

    def event_key_release(self, key):
        if self.human:
            if key in jump_key[self.player]:
                self.jump_release()

    def event_joystick(self, js_name, js_id, input_type, input_id, value):
        if self.human:
            js = (js_id, input_type, input_id)
            if value >= joystick_threshold:
                if js in jump_js[self.player]:
                    self.jump()
                if js in action_js[self.player]:
                    self.action()
                if js in up_js[self.player]:
                    self.press_up()
                if js in pause_js[self.player] or js in menu_js[self.player]:
                    sge.game.current_room.pause()
            else:
                if js in jump_js[self.player]:
                    self.jump_release()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, Death):
            self.kill()
        elif isinstance(other, LevelEnd):
            sge.game.current_room.win_level()
            other.destroy()
        elif isinstance(other, Explosion):
            other.touch(self)
        elif isinstance(other, InteractiveObject):
            if (ydirection == 1 or
                    (xdirection and not ydirection and
                     self.bbox_bottom - other.bbox_top <= STOMP_LAX)):
                other.stomp(self)
            # This check is necessary to allow the player to drop held
            # objects. It also has a nice side-effect of preventing the
            # player from being hurt by the same object more than once
            # until the collision stops.
            elif xdirection or ydirection:
                other.touch(self)
        elif isinstance(other, HiddenItemBlock):
            if ydirection == -1 and not xdirection:
                move_loss = max(0, other.bbox_bottom - self.bbox_top)
                self.move_y(move_loss, absolute=True, do_events=False)
                self.event_physics_collision_top(other, move_loss)

    def event_physics_collision_left(self, other, move_loss):
        for block in self.get_left_touching_wall():
            if isinstance(block, HurtRight):
                self.hurt()
            elif isinstance(block, RockWall):
                rock = block.parent()
                if rock is not None:
                    rock.touch(self)

        if isinstance(other, xsge_physics.SolidRight):
            self.xvelocity = max(self.xvelocity, 0)

        if self.left_pressed:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "left" and self.bbox_left == warp.x and
                        abs(self.y - warp.y) < WARP_LAX):
                    warp.warp(self)

    def event_physics_collision_right(self, other, move_loss):
        for block in self.get_right_touching_wall():
            if isinstance(block, HurtLeft):
                self.hurt()
            elif isinstance(block, RockWall):
                rock = block.parent()
                if rock is not None:
                    rock.touch(self)

        if isinstance(other, xsge_physics.SolidLeft):
            self.xvelocity = min(self.xvelocity, 0)

        if self.right_pressed:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "right" and self.bbox_right == warp.x and
                        abs(self.y - warp.y) < WARP_LAX):
                    warp.warp(self)

    def event_physics_collision_top(self, other, move_loss):
        top_touching = self.get_top_touching_wall()

        for hblock in self.collision(HiddenItemBlock, y=(self.y - 1)):
            if not self.collision(hblock):
                hblock.hit(self)

        tmv = 0
        for i in six.moves.range(CEILING_LAX):
            if (not self.get_left_touching_wall() and
                    not self.get_left_touching_slope()):
                self.x -= 1
                tmv -= 1
                if (not self.get_top_touching_wall() and
                        not self.get_top_touching_slope()):
                    self.move_y(-move_loss)
                    break
        else:
            self.x -= tmv
            tmv = 0
            for i in six.moves.range(CEILING_LAX):
                if (not self.get_left_touching_wall() and
                        not self.get_left_touching_slope()):
                    self.x += 1
                    tmv += 1
                    if (not self.get_top_touching_wall() and
                            not self.get_top_touching_slope()):
                        self.move_y(-move_loss)
                        break
            else:
                self.x -= tmv
                tmv = 0
                self.yvelocity = max(self.yvelocity, 0)

        for block in top_touching:
            if isinstance(block, HittableBlock):
                block.hit(self)
            elif isinstance(block, HurtBottom):
                self.hurt()
            elif isinstance(block, RockWall):
                rock = block.parent()
                if rock is not None:
                    rock.touch(self)

        if self.up_pressed:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "up" and self.bbox_top == warp.y and
                        abs(self.x - warp.x) < WARP_LAX):
                    warp.warp(self)
                    break

    def event_physics_collision_bottom(self, other, move_loss):
        for block in self.get_bottom_touching_wall():
            if isinstance(block, HurtTop):
                self.hurt()

        if isinstance(other, xsge_physics.SolidTop):
            self.yvelocity = min(self.yvelocity, 0)
        elif isinstance(other, (xsge_physics.SlopeTopLeft,
                                xsge_physics.SlopeTopRight)):
            self.yvelocity = min(self.slide_speed * (other.bbox_height /
                                                     other.bbox_width),
                                 self.yvelocity)

        if self.down_pressed:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "down" and self.bbox_bottom == warp.y and
                        abs(self.x - warp.x) < WARP_LAX):
                    warp.warp(self)


class DeadMan(sge.dsp.Object):

    """Object which falls off the screen, then gets destroyed."""

    gravity = GRAVITY
    fall_speed = PLAYER_DIE_FALL_SPEED

    def event_begin_step(self, time_passed, delta_mult):
        if self.yvelocity < self.fall_speed:
            self.yacceleration = self.gravity
        else:
            self.yvelocity = self.fall_speed
            self.yacceleration = 0

    def event_step(self, time_passed, delta_mult):
        if self.y - self.image_origin_y > sge.game.current_room.height:
            self.destroy()


class Corpse(xsge_physics.Collider):

    """Like DeadMan, but just falls to the floor, not off-screen."""

    gravity = GRAVITY
    fall_speed = ENEMY_FALL_SPEED

    def event_create(self):
        self.alarms["die"] = 90

    def event_begin_step(self, time_passed, delta_mult):
        if self.get_bottom_touching_wall() or self.get_bottom_touching_slope():
            self.yvelocity = 0
        else:
            if self.yvelocity < self.fall_speed:
                self.yacceleration = self.gravity
            else:
                self.yvelocity = min(self.yvelocity, self.fall_speed)
                self.yacceleration = 0

    def event_alarm(self, alarm_id):
        if alarm_id == "die":
            self.destroy()


class Smoke(sge.dsp.Object):

    def event_animation_end(self):
        self.destroy()


class InteractiveObject(sge.dsp.Object):

    active_range = ENEMY_ACTIVE_RANGE
    killed_by_void = True
    always_active = False
    never_active = False
    always_tangible = False
    never_tangible = False
    knockable = False
    burnable = False
    freezable = False
    blastable = False
    activated = False
    parent = None
    warping = False

    def activate(self):
        self.activated = True
        if not self.never_tangible:
            self.tangible = True
        if not self.never_active:
            self.active = True

    def deactivate(self):
        self.activated = False
        if not self.always_active:
            self.active = False
        if not self.always_tangible:
            self.tangible = False

    def update_active(self):
        if not self.warping:
            for view in sge.game.current_room.views:
                if (self.bbox_left <= (view.x + view.width +
                                       self.active_range) and
                        self.bbox_right >= view.x - self.active_range and
                        self.bbox_top <= (view.y + view.height +
                                          self.active_range) and
                        self.bbox_bottom >= view.y - self.active_range):
                    if not self.activated:
                        self.activate()
                    break
            else:
                if self.activated:
                    self.deactivate()

            void_y = sge.game.current_room.height + self.active_range
            if self.killed_by_void and self.bbox_top > void_y:
                self.destroy()

    def get_nearest_player(self):
        player = None
        dist = 0
        for obj in sge.game.current_room.objects:
            if isinstance(obj, Player):
                ndist = math.hypot(self.x - obj.x, self.y - obj.y)
                if player is None or ndist < dist:
                    player = obj
                    dist = ndist
        return player

    def set_direction(self, direction):
        self.image_xscale = abs(self.image_xscale) * direction

    def move(self):
        pass

    def touch(self, other):
        pass

    def stomp(self, other):
        self.touch(other)

    def knock(self, other=None):
        pass

    def burn(self):
        pass

    def freeze(self):
        pass

    def blast(self):
        self.burn()

    def kick(self):
        self.drop()

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None

    def kick_up(self):
        self.kick()

    def touch_death(self):
        if self.parent is None:
            play_sound(fall_sound, self.x, self.y)
            DeadMan.create(self.x, self.y, self.z, sprite=self.sprite,
                           xvelocity=self.xvelocity, yvelocity=0,
                           image_xscale=self.image_xscale,
                           image_yscale=-abs(self.image_yscale))
            self.destroy()

    def project_light(self):
        pass

    def event_create(self):
        InteractiveObject.deactivate(self)

    def event_begin_step(self, time_passed, delta_mult):
        if not self.warping:
            self.move()
        elif self.xvelocity:
            self.image_xscale = math.copysign(self.image_xscale, self.xvelocity)

    def event_step(self, time_passed, delta_mult):
        self.update_active()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, Death):
            self.touch_death()

    def event_destroy(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None


class InteractiveCollider(InteractiveObject, xsge_physics.Collider):

    def deactivate(self):
        tangible_anyway = False
        if not self.never_tangible:
            for other in self.get_bottom_touching_wall():
                if isinstance(other, xsge_physics.MobileWall):
                    tangible_anyway = True
                    break

        super(InteractiveCollider, self).deactivate()
        if tangible_anyway:
            self.tangible = True

    def stop_left(self):
        self.xvelocity = 0

    def stop_right(self):
        self.xvelocity = 0

    def stop_up(self):
        self.yvelocity = 0

    def stop_down(self):
        self.yvelocity = 0

    def touch_hurt(self):
        self.touch_death()

    def event_physics_collision_left(self, other, move_loss):
        if isinstance(other, HurtRight):
            self.touch_hurt()

        if isinstance(other, xsge_physics.SolidRight):
            self.stop_left()
        elif isinstance(other, xsge_physics.SlopeTopRight):
            if self.yvelocity > 0:
                self.stop_down()
        elif isinstance(other, xsge_physics.SlopeBottomRight):
            if self.yvelocity < 0:
                self.stop_up()

    def event_physics_collision_right(self, other, move_loss):
        if isinstance(other, HurtLeft):
            self.touch_hurt()

        if isinstance(other, xsge_physics.SolidLeft):
            self.stop_right()
        elif isinstance(other, xsge_physics.SlopeTopLeft):
            if self.yvelocity > 0:
                self.stop_down()
        elif isinstance(other, xsge_physics.SlopeBottomLeft):
            if self.yvelocity < 0:
                self.stop_up()

    def event_physics_collision_top(self, other, move_loss):
        if isinstance(other, HurtBottom):
            self.touch_hurt()
        if isinstance(other, (xsge_physics.SolidBottom,
                              xsge_physics.SlopeBottomLeft,
                              xsge_physics.SlopeBottomRight)):
            self.stop_up()

    def event_physics_collision_bottom(self, other, move_loss):
        if isinstance(other, HurtTop):
            self.touch_hurt()
        if isinstance(other, (xsge_physics.SolidTop, xsge_physics.SlopeTopLeft,
                              xsge_physics.SlopeTopRight)):
            self.stop_down()


class WinPuffObject(InteractiveObject):

    win_puff_score = ENEMY_KILL_POINTS

    def win_puff(self):
        play_sound(pop_sound, self.x, self.y)
        if self.sprite is None:
            x = self.x
            y = self.y
        else:
            x = self.x - self.image_origin_x + self.sprite.width / 2
            y = self.y - self.image_origin_y + self.sprite.height / 2
        Smoke.create(x, y, self.z, sprite=smoke_plume_sprite)
        self.destroy()
        sge.game.current_room.add_points(self.win_puff_score)


class FallingObject(InteractiveCollider):

    """
    Falls based on gravity. If on a slope, falls at a constant speed
    based on the steepness of the slope.
    """

    gravity = GRAVITY
    fall_speed = ENEMY_FALL_SPEED
    slide_speed = ENEMY_SLIDE_SPEED

    was_on_floor = False

    def move(self):
        on_floor = self.get_bottom_touching_wall()
        on_slope = self.get_bottom_touching_slope()
        if self.was_on_floor and (on_floor or on_slope) and self.yvelocity >= 0:
            self.yacceleration = 0
            if on_floor:
                if self.yvelocity > 0:
                    self.yvelocity = 0
                    self.stop_down()
            elif on_slope:
                self.yvelocity = self.slide_speed * (on_slope[0].bbox_height /
                                                     on_slope[0].bbox_width)
        else:
            if self.yvelocity < self.fall_speed:
                self.yacceleration = self.gravity
            else:
                self.yvelocity = self.fall_speed
                self.yacceleration = 0

        self.was_on_floor = on_floor or on_slope


class WalkingObject(FallingObject):

    """
    Walks toward the player.  Turns around at walls, and can also be set
    to turn around at ledges with the stayonplatform attribute.
    """

    walk_speed = ENEMY_WALK_SPEED
    stayonplatform = False

    def deactivate(self):
        super(WalkingObject, self).deactivate()
        self.xvelocity = 0

    def set_direction(self, direction):
        self.xvelocity = self.walk_speed * direction
        self.image_xscale = abs(self.image_xscale) * direction

    def move(self):
        super(WalkingObject, self).move()

        if not self.xvelocity:
            player = self.get_nearest_player()
            if player is not None:
                self.set_direction(1 if self.x < player.x else -1)
            else:
                self.set_direction(-1)

        on_floor = self.get_bottom_touching_wall()
        on_slope = self.get_bottom_touching_slope()
        if (on_floor or on_slope) and self.stayonplatform:
            if self.xvelocity < 0:
                for tile in on_floor:
                    if tile.bbox_left < self.x:
                        break
                else:
                    if not on_slope:
                        self.set_direction(1)
            else:
                for tile in on_floor:
                    if tile.bbox_right > self.x:
                        break
                else:
                    if not on_slope:
                        self.set_direction(-1)

    def stop_left(self):
        self.set_direction(1)

    def stop_right(self):
        self.set_direction(-1)


class CrowdBlockingObject(InteractiveObject):

    """Blocks CrowdObject instances, causing them to turn around."""

    pass


class CrowdObject(WalkingObject, CrowdBlockingObject):

    """
    Turns around when colliding with a CrowdBlockingObject.  (Note: this
    class is itself derived from CrowdBlockingObject.)
    """

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, CrowdBlockingObject):
            if xdirection:
                self.set_direction(-xdirection)
            else:
                if self.x > other.x:
                    self.set_direction(1)
                elif self.x < other.x:
                    self.set_direction(-1)
                elif id(self) > id(other):
                    self.set_direction(1)
                else:
                    self.set_direction(-1)
        else:
            super(CrowdObject, self).event_collision(other, xdirection,
                                                     ydirection)


class KnockableObject(InteractiveObject):

    """Provides basic knocking behavior."""

    knockable = True
    blastable = True

    def knock(self, other=None):
        play_sound(fall_sound, self.x, self.y)
        DeadMan.create(self.x, self.y, self.z, sprite=self.sprite,
                       xvelocity=self.xvelocity,
                       yvelocity=get_jump_speed(ENEMY_HIT_BELOW_HEIGHT),
                       image_xscale=self.image_xscale,
                       image_yscale=-abs(self.image_yscale))
        self.destroy()


class BurnableObject(InteractiveObject):

    """Provides basic burn behavior."""

    burnable = True
    blastable = True

    def burn(self):
        play_sound(fall_sound, self.x, self.y)
        DeadMan.create(self.x, self.y, self.z, sprite=self.sprite,
                       xvelocity=self.xvelocity, yvelocity=0,
                       image_xscale=self.image_xscale,
                       image_yscale=-abs(self.image_yscale))
        self.destroy()


class FreezableObject(InteractiveObject):

    """Provides basic freeze behavior."""

    freezable = True
    frozen_sprite = None
    frozen_time = THAW_TIME_DEFAULT
    frozen = False

    def update_active(self):
        if self.frozen:
            self.active = False
        else:
            super(FreezableObject, self).update_active()

    def permafreeze(self):
        prev_frozen_time = self.frozen_time
        self.frozen_time = None
        self.freeze()
        self.frozen_time = prev_frozen_time

    def freeze(self):
        if self.frozen_sprite is None:
            self.frozen_sprite = sge.gfx.Sprite(
                width=self.sprite.width, height=self.sprite.height,
                origin_x=self.sprite.origin_x, origin_y=self.sprite.origin_y,
                fps=THAW_FPS, bbox_x=self.sprite.bbox_x,
                bbox_y=self.sprite.bbox_y, bbox_width=self.sprite.bbox_width,
                bbox_height=self.sprite.bbox_height)
            self.frozen_sprite.append_frame()
            self.frozen_sprite.draw_sprite(self.sprite, self.image_index,
                                           self.sprite.origin_x,
                                           self.sprite.origin_y)
            colorizer = sge.gfx.Sprite(width=self.frozen_sprite.width,
                                       height=self.frozen_sprite.height)
            colorizer.draw_rectangle(0, 0, colorizer.width, colorizer.height,
                                     fill=sge.gfx.Color((128, 128, 255)))
            self.frozen_sprite.draw_sprite(colorizer, 0, 0, 0, frame=0,
                                           blend_mode=sge.BLEND_RGB_MULTIPLY)

        frozen_self = FrozenObject.create(self.x, self.y, self.z,
                                          sprite=self.frozen_sprite,
                                          image_fps=0,
                                          image_xscale=self.image_xscale,
                                          image_yscale=self.image_yscale)
        frozen_self.unfrozen = self
        self.frozen = True
        self.tangible = False
        self.active = False
        self.visible = False
        if self.frozen_time is not None:
            frozen_self.alarms["thaw_warn"] = self.frozen_time


class FrozenObject(InteractiveObject, xsge_physics.Solid):

    always_active = True
    always_tangible = True
    burnable = True
    freezable = True
    blastable = True
    unfrozen = None

    def thaw(self):
        if self.unfrozen is not None:
            self.unfrozen.frozen = False
            self.unfrozen.tangible = True
            self.unfrozen.visible = True
            self.unfrozen.activate()
        self.destroy()

    def burn(self):
        self.thaw()
        play_sound(sizzle_sound, self.x, self.y)

    def freeze(self):
        if self.unfrozen is not None:
            self.thaw()
            self.unfrozen.freeze()

    def event_alarm(self, alarm_id):
        if self.unfrozen is not None:
            if alarm_id == "thaw_warn":
                self.image_fps = None
                self.alarms["thaw"] = THAW_WARN_TIME
            elif alarm_id == "thaw":
                self.thaw()


class WalkingSnowball(CrowdObject, KnockableObject, BurnableObject,
                      WinPuffObject):

    freezable = True

    def __init__(self, x, y, z=0, **kwargs):
        kwargs["sprite"] = snowball_walk_sprite
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.stomp_jump(self)
        play_sound(squish_sound, self.x, self.y)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)
        Corpse.create(self.x, self.y, self.z, sprite=snowball_squished_sprite,
                      image_xscale=self.image_xscale,
                      image_yscale=self.image_yscale)
        self.destroy()

    def knock(self, other=None):
        super(WalkingSnowball, self).knock(other)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def burn(self):
        super(WalkingSnowball, self).burn()
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def freeze(self):
        self.burn()


class BouncingSnowball(WalkingSnowball):

    def __init__(self, x, y, z=0, **kwargs):
        kwargs["sprite"] = bouncing_snowball_sprite
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)

    def stop_up(self):
        self.yvelocity = 0

    def stop_down(self):
        self.yvelocity = get_jump_speed(SNOWBALL_BOUNCE_HEIGHT, self.gravity)


class WalkingIceblock(CrowdObject, KnockableObject, BurnableObject,
                      WinPuffObject):

    gravity = ICEBLOCK_GRAVITY
    fall_speed = ICEBLOCK_FALL_SPEED
    freezable = True
    stayonplatform = True

    def __init__(self, x, y, z=0, start_flat=False, **kwargs):
        self.start_flat = start_flat
        kwargs["sprite"] = iceblock_walk_sprite
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)
        self.flat = False
        self.dashing = False
        self.thrower = None

    def init_flat(self):
        self.flat = True
        self.dashing = False
        self.active_range = ICEBLOCK_ACTIVE_RANGE
        self.walk_speed = self.__class__.walk_speed
        self.stayonplatform = False
        self.xvelocity = 0
        self.xdeceleration = 0
        self.sprite = iceblock_flat_sprite
        self.image_index = 0
        self.image_fps = None

    def cancel_flat(self):
        self.flat = False
        self.dashing = False
        self.active_range = self.__class__.active_range
        self.walk_speed = self.__class__.walk_speed
        self.stayonplatform = True
        self.xvelocity = 0
        self.xdeceleration = 0
        self.sprite = iceblock_walk_sprite
        self.image_index = 0
        self.image_fps = None

    def init_dash(self, direction):
        self.flat = True
        self.dashing = True
        self.active_range = ICEBLOCK_ACTIVE_RANGE
        self.walk_speed = ICEBLOCK_DASH_SPEED
        self.xvelocity = 0
        self.xdeceleration = 0
        self.sprite = iceblock_flat_sprite
        self.image_index = 0
        self.image_fps = None
        self.set_direction(direction)

    def cancel_dash(self):
        self.flat = True
        self.dashing = False
        self.active_range = ICEBLOCK_ACTIVE_RANGE
        self.walk_speed = self.__class__.walk_speed
        self.sprite = iceblock_flat_sprite
        self.image_index = 0
        self.image_fps = 0

    def move(self):
        if not self.flat or self.dashing:
            super(WalkingIceblock, self).move()
        else:
            FallingObject.move(self)

    def deactivate(self):
        if self.dashing:
            self.destroy()
        else:
            super(WalkingIceblock, self).deactivate()

    def touch(self, other):
        if self.flat and not self.dashing:
            if self.parent is None:
                self.thrower = other
                if other.pickup(self):
                    self.gravity = 0
                    if other.action_pressed:
                        other.action()
                else:
                    other.do_kick()
                    self.init_dash(-1 if other.image_xscale < 0 else 1)
        else:
            other.hurt()

    def stomp(self, other):
        if not self.flat or self.dashing:
            other.stomp_jump(self)
            play_sound(stomp_sound, self.x, self.y)
            self.init_flat()
        else:
            self.touch(other)

    def knock(self, other=None):
        if self.parent is None:
            super(WalkingIceblock, self).knock(other)
            sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def burn(self):
        super(WalkingIceblock, self).burn()
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def freeze(self):
        if self.dashing:
            self.cancel_dash()
        elif self.flat:
            self.cancel_flat()

    def stop_left(self):
        if self.flat and self.parent is None:
            play_sound(iceblock_bump_sound, self.x, self.y)
            self.xvelocity = abs(self.xvelocity)
            self.set_direction(1)

            left_touching = self.get_left_touching_wall()
            for hblock in self.collision(HiddenItemBlock, x=(self.x - 1)):
                if not self.collision(hblock):
                    left_touching.append(hblock)

            for block in left_touching:
                if isinstance(block, HittableBlock):
                    block.hit(self.thrower)
        else:
            super(WalkingIceblock, self).stop_left()

    def stop_right(self):
        if self.flat and self.parent is None:
            play_sound(iceblock_bump_sound, self.x, self.y)
            self.xvelocity = -abs(self.xvelocity)
            self.set_direction(-1)

            right_touching = self.get_right_touching_wall()
            for hblock in self.collision(HiddenItemBlock, x=(self.x + 1)):
                if not self.collision(hblock):
                    right_touching.append(hblock)

            for block in right_touching:
                if isinstance(block, HittableBlock):
                    block.hit(self.thrower)
        else:
            super(WalkingIceblock, self).stop_right()

    def stop_up(self):
        self.yvelocity = 0
        if self.flat and self.parent is None:
            top_touching = self.get_top_touching_wall()
            for hblock in self.collision(HiddenItemBlock, y=(self.y - 1)):
                if not self.collision(hblock):
                    top_touching.append(hblock)

            for block in top_touching:
                if isinstance(block, HittableBlock):
                    block.hit(self.thrower)

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None
            self.gravity = self.__class__.gravity

    def kick(self):
        if self.parent is not None:
            self.parent.kick_object()
            self.gravity = self.__class__.gravity
            self.init_dash(-1 if self.parent.image_xscale < 0 else 1)
            self.yvelocity = 0
            self.parent = None

    def kick_up(self):
        if self.parent is not None:
            self.parent.kick_object()
            play_sound(kick_sound, self.x, self.y)
            self.gravity = self.__class__.gravity
            self.xvelocity = self.parent.xvelocity
            self.yvelocity = get_jump_speed(KICK_UP_HEIGHT, self.gravity)
            self.parent = None

    def event_create(self):
        super(WalkingIceblock, self).event_create()
        if self.start_flat:
            self.init_flat()

    def event_end_step(self, time_passed, delta_mult):
        if self.parent is None:
            if (self.flat and not self.dashing and self.yvelocity >= 0 and
                (self.get_bottom_touching_wall() or
                 self.get_bottom_touching_slope())):
                self.xdeceleration = ICEBLOCK_FRICTION
            else:
                self.xdeceleration = 0

    def event_collision(self, other, xdirection, ydirection):
        if self.parent is None:
            if self.flat:
                if isinstance(other, InteractiveObject) and other.knockable:
                    if (self.dashing or abs(self.xvelocity) > 0.05 or
                            self.yvelocity < 0 or (not self.was_on_floor and
                                                   self.yvelocity > 0.05)):
                        other.knock(self)
                elif isinstance(other, Coin):
                    other.event_collision(self.thrower, -xdirection,
                                          -ydirection)
                elif isinstance(other, HiddenItemBlock):
                    if ydirection == -1:
                        self.move_y(max(0, other.bbox_bottom - self.bbox_top),
                                    absolute=True, do_events=False)
                        self.stop_up()
                    elif xdirection == -1:
                        self.move_x(max(0, other.bbox_right - self.bbox_left),
                                    absolute=True, do_events=False)
                        self.stop_left()
                    elif xdirection == 1:
                        self.move_x(min(0, other.bbox_left - self.bbox_right),
                                    absolute=True, do_events=False)
                        self.stop_right()
                elif isinstance(other, Death):
                    self.touch_death()
            else:
                super(WalkingIceblock, self).event_collision(other, xdirection,
                                                             ydirection)


class Spiky(CrowdObject, KnockableObject, FreezableObject, WinPuffObject):

    burnable = True
    blastable = True
    stayonplatform = True

    def __init__(self, x, y, z=0, start_frozen=False, **kwargs):
        self.start_frozen = start_frozen
        kwargs["sprite"] = spiky_walk_sprite
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)
        self.frozen_sprite = spiky_iced_sprite

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.hurt()

    def knock(self, other=None):
        super(Spiky, self).knock(other)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def blast(self):
        self.knock()

    def touch_hurt(self):
        pass

    def event_create(self):
        super(Spiky, self).event_create()
        if self.start_frozen:
            self.permafreeze()


class WalkingBomb(CrowdObject, KnockableObject, FreezableObject,
                  WinPuffObject):

    burnable = True
    blastable = True
    stayonplatform = True

    def __init__(self, x, y, z=0, start_frozen=False, start_ticking=False,
                 **kwargs):
        self.start_frozen = start_frozen
        self.start_ticking = start_ticking
        kwargs["sprite"] = bomb_walk_sprite
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)
        self.frozen_sprite = bomb_iced_sprite
        self.ticking = False
        self.thrower = None
        self.normal_gravity = self.__class__.gravity

    def init_ticking(self):
        self.ticking = True
        self.active_range = ICEBLOCK_ACTIVE_RANGE
        self.normal_gravity = BOMB_GRAVITY
        self.gravity = self.normal_gravity
        self.xvelocity = 0
        self.sprite = bomb_ticking_sprite
        self.image_index = 0
        self.image_fps = None

    def cancel_ticking(self):
        self.ticking = False
        self.active_range = self.__class__.active_range
        self.normal_gravity = self.__class__.gravity
        self.gravity = self.normal_gravity
        self.xvelocity = 0
        self.sprite = bomb_walk_sprite
        self.image_index = 0
        self.image_fps = None

    def set_direction(self, direction):
        if self.ticking:
            self.image_xscale = abs(self.image_xscale) * direction
            self.xvelocity = abs(self.xvelocity) * direction / 2
        else:
            super(WalkingBomb, self).set_direction(direction)

    def move(self):
        if not self.ticking:
            super(WalkingBomb, self).move()
        else:
            FallingObject.move(self)

    def touch(self, other):
        if self.ticking:
            if other.pickup(self):
                self.thrower = other
                self.gravity = 0
                self.xvelocity = 0
                self.yvelocity = 0
                if other.action_pressed:
                    other.action()
        else:
            other.hurt()

    def stomp(self, other):
        if self.ticking:
            self.touch(other)
        else:
            other.stomp_jump(self)
            play_sound(stomp_sound, self.x, self.y)
            self.init_ticking()
            self.thrower = other

    def knock(self, other=None):
        if isinstance(other, Player):
            self.thrower = other
            self.burn()
        elif isinstance(other, WalkingIceblock):
            self.thrower = other.thrower
            self.burn()
        elif isinstance(other, FallingIcicle):
            super(WalkingBomb, self).knock(other)
            sge.game.current_room.add_points(ENEMY_KILL_POINTS)
        else:
            self.burn()

    def burn(self):
        e = Explosion.create(self.x, self.y, self.z, sprite=explosion_sprite)
        e.detonator = self.thrower
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)
        self.destroy()

    def freeze(self):
        if self.ticking:
            if self.image_index > 0:
                self.image_index -= 1
            elif self.parent is None:
                self.cancel_ticking()
        else:
            super(WalkingBomb, self).freeze()

    def touch_hurt(self):
        pass

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None
            self.gravity = self.normal_gravity

    def kick(self):
        if self.parent is not None:
            self.parent.kick_object()
            self.xvelocity = math.copysign(KICK_FORWARD_SPEED,
                                           self.parent.image_xscale)
            self.yvelocity = get_jump_speed(KICK_FORWARD_HEIGHT,
                                            self.normal_gravity)
            self.parent = None
            self.gravity = self.normal_gravity

    def kick_up(self):
        if self.parent is not None:
            self.parent.kick_object()
            self.xvelocity = self.parent.xvelocity
            self.yvelocity = get_jump_speed(KICK_UP_HEIGHT,
                                            self.normal_gravity)
            self.parent = None
            self.gravity = self.normal_gravity

    def stop_left(self):
        if self.ticking:
            if self.parent is None:
                self.set_direction(1)
        else:
            super(WalkingBomb, self).stop_left()

    def stop_right(self):
        if self.ticking:
            if self.parent is None:
                self.set_direction(-1)
        else:
            super(WalkingBomb, self).stop_right()

    def stop_up(self):
        if self.parent is None:
            self.yvelocity = 0

    def event_create(self):
        super(WalkingBomb, self).event_create()
        if self.start_ticking:
            self.init_ticking()
        if self.start_frozen:
            self.permafreeze()

    def event_end_step(self, time_passed, delta_mult):
        if (self.ticking and self.yvelocity >= 0 and
                (self.get_bottom_touching_wall() or
                 self.get_bottom_touching_slope())):
            self.xdeceleration = ROCK_FRICTION
        else:
            self.xdeceleration = 0

    def event_animation_end(self):
        if self.ticking:
            self.burn()


class Jumpy(CrowdObject, KnockableObject, FreezableObject, WinPuffObject):

    nonstick_left = True
    nonstick_right = True
    nonstick_top = True
    nonstick_bottom = True
    burnable = True
    blastable = True
    walk_speed = 0

    def __init__(self, x, y, z=0, start_frozen=False, **kwargs):
        self.start_frozen = start_frozen
        kwargs["sprite"] = jumpy_sprite
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)
        self.frozen_sprite = jumpy_iced_sprite

    def move(self):
        super(Jumpy, self).move()

        y = self.y + (jumpy_sprite.height - jumpy_bounce_sprite.height)
        for obj in self.collision(xsge_physics.SolidTop, y=y):
            if not self.collision(obj):
                self.sprite = jumpy_bounce_sprite
                break
        else:
            self.sprite = jumpy_sprite

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.hurt()

    def knock(self, other=None):
        super(Jumpy, self).knock(other)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def blast(self):
        self.knock()

    def touch_hurt(self):
        pass

    def stop_up(self):
        self.yvelocity = 0

    def stop_down(self):
        self.yvelocity = get_jump_speed(JUMPY_BOUNCE_HEIGHT, self.gravity)

    def event_create(self):
        super(Jumpy, self).event_create()
        if self.start_frozen:
            self.permafreeze()


class FlyingEnemy(CrowdBlockingObject):

    def move(self):
        if abs(self.xvelocity) > abs(self.yvelocity):
            self.image_xscale = math.copysign(self.image_xscale, self.xvelocity)
            self.had_xv = 5
        elif self.had_xv > 0:
            self.had_xv -= 1
        else:
            player = self.get_nearest_player()
            if player is not None:
                if self.x < player.x:
                    self.image_xscale = abs(self.image_xscale)
                else:
                    self.image_xscale = -abs(self.image_xscale)


class FlyingSnowball(FlyingEnemy, KnockableObject, BurnableObject,
                     WinPuffObject):

    killed_by_void = False
    always_active = True
    freezable = True
    had_xv = 0

    def __init__(self, x, y, z=0, **kwargs):
        kwargs["sprite"] = flying_snowball_sprite
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.stomp_jump(self)
        play_sound(squish_sound, self.x, self.y)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)
        Corpse.create(self.x, self.y, self.z,
                      sprite=flying_snowball_squished_sprite,
                      image_xscale=self.image_xscale,
                      image_yscale=self.image_yscale)
        self.destroy()

    def knock(self, other=None):
        super(FlyingSnowball, self).knock(other)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def burn(self):
        super(FlyingSnowball, self).burn()
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def freeze(self):
        self.burn()


class FlyingSpiky(FlyingEnemy, KnockableObject, FreezableObject,
                  WinPuffObject):

    killed_by_void = False
    always_active = True
    burnable = True
    had_xv = 0

    def __init__(self, x, y, z=0, start_frozen=False, **kwargs):
        self.start_frozen = start_frozen
        kwargs["sprite"] = flying_spiky_sprite
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)
        self.frozen_sprite = flying_spiky_iced_sprite

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.hurt()

    def knock(self, other=None):
        super(FlyingSpiky, self).knock(other)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def event_create(self):
        super(FlyingSpiky, self).event_create()
        if self.start_frozen:
            self.permafreeze()


class Explosion(InteractiveObject):

    killed_by_void = False
    detonator = None

    def event_create(self):
        super(Explosion, self).event_create()
        self.__life = EXPLOSION_TIME
        self.__friends = set()
        play_sound(explosion_sound, self.x, self.y)

    def deactivate(self):
        pass

    def update_active(self):
        self.active = True
        self.tangible = True

    def touch(self, other):
        other.hurt()

    def project_light(self):
        xsge_lighting.project_light(self.x, self.y, explosion_light_sprite)

    def event_step(self, time_passed, delta_mult):
        self.__life -= delta_mult
        if self.__life <= 0:
            self.destroy()

    def event_collision(self, other, xdirection, ydirection):
        if other not in (friend() for friend in self.__friends):
            self.__friends.add(weakref.ref(other))
            if isinstance(other, InteractiveObject):
                if other.blastable:
                    other.blast()
            if isinstance(other, HittableBlock):
                if self.detonator is not None:
                    other.hit(self.detonator)
                else:
                    detonator = self.get_nearest_player()
                    if detonator is not None:
                        other.hit(detonator)
                    else:
                        other.hit(None)
            if isinstance(other, (Iceblock)):
                other.burn()
            if isinstance(other, (ThinIce)):
                other.shatter()

        super(Explosion, self).event_collision(other, xdirection, ydirection)


class Icicle(InteractiveObject):

    shaking = False

    def __init__(self, x, y, z=0, **kwargs):
        kwargs["sprite"] = icicle_sprite
        kwargs["checks_collisions"] = False
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)
        self.shake_counter = SHAKE_FRAME_TIME

    def do_shake(self):
        self.shaking = True
        play_sound(icicle_shake_sound, self.x, self.y)
        self.alarms["fall"] = ICICLE_SHAKE_TIME

    def check_shake(self):
        if not self.warping:
            players = []
            crash_y = sge.game.current_room.height
            objects = (
                sge.game.current_room.get_objects_at(
                    self.bbox_left - ICICLE_LAX, self.bbox_bottom,
                    self.bbox_width + 2 * ICICLE_LAX,
                    (sge.game.current_room.height - self.bbox_bottom +
                     sge.game.current_room.object_area_height)) |
                sge.game.current_room.object_area_void)
            for obj in objects:
                if (obj.bbox_top > self.bbox_bottom and
                        self.bbox_right > obj.bbox_left and
                        self.bbox_left < obj.bbox_right):
                    if isinstance(obj, xsge_physics.SolidTop):
                        crash_y = min(crash_y, obj.bbox_top)
                    elif isinstance(obj, xsge_physics.SlopeTopLeft):
                        crash_y = min(crash_y, obj.get_slope_y(self.bbox_right))
                    elif isinstance(obj, xsge_physics.SlopeTopRight):
                        crash_y = min(crash_y, obj.get_slope_y(self.bbox_left))
                if (obj.bbox_bottom > self.bbox_top and
                        self.bbox_right + ICICLE_LAX > obj.bbox_left and
                        self.bbox_left - ICICLE_LAX < obj.bbox_right):
                    if isinstance(obj, Player):
                        players.append(obj)

            for player in players:
                if player.bbox_top < crash_y:
                    self.do_shake()
                    break

    def deactivate(self):
        self.shaking = False
        super(Icicle, self).deactivate()

    def touch(self, other):
        other.hurt()

    def event_step(self, time_passed, delta_mult):
        super(Icicle, self).event_step(time_passed, delta_mult)

        if self.active:
            if self.shaking:
                self.shake_counter -= delta_mult
                while self.shake_counter <= 0:
                    self.shake_counter += SHAKE_FRAME_TIME
                    if self.image_origin_x > self.sprite.origin_x:
                        self.image_origin_x = self.sprite.origin_x - 2
                    else:
                        self.image_origin_x = self.sprite.origin_x + 2
            else:
                self.check_shake()

    def event_alarm(self, alarm_id):
        if alarm_id == "fall":
            FallingIcicle.create(self.x, self.y, self.z, sprite=self.sprite,
                                 image_xscale=self.image_xscale,
                                 image_yscale=self.image_yscale)
            self.destroy()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, InteractiveObject) and other.knockable:
            other.knock(self)

        super(Icicle, self).event_collision(other, xdirection, ydirection)


class SteadyIcicle(Icicle):

    def check_shake(self, earthquake=False):
        if earthquake:
            super(SteadyIcicle, self).check_shake()


class RaccotIcicle(Icicle):

    never_tangible = True

    def __init__(self, x, y, z=0, **kwargs):
        kwargs["visible"] = False
        super(RaccotIcicle, self).__init__(x, y, z, **kwargs)

    def check_shake(self, raccot=False):
        if raccot:
            super(RaccotIcicle, self).check_shake()

    def do_shake(self):
        FallingIcicle.create(self.x, self.y, self.z, sprite=self.sprite,
                             image_xscale=self.image_xscale,
                             image_yscale=self.image_yscale)


class FallingIcicle(FallingObject):

    gravity = ICICLE_GRAVITY
    fall_speed = ICICLE_FALL_SPEED

    def deactivate(self):
        self.destroy()

    def touch(self, other):
        other.hurt()

    def touch_death(self):
        play_sound(sizzle_sound, self.x, self.y)
        self.destroy()

    def touch_hurt(self):
        pass

    def stop_down(self):
        play_sound(icicle_crash_sound, self.x, self.y)
        Corpse.create(self.x, self.y, self.z,
                      sprite=icicle_broken_sprite,
                      image_xscale=self.image_xscale,
                      image_yscale=self.image_yscale)
        self.destroy()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, InteractiveObject) and other.knockable:
            other.knock(self)

        super(FallingIcicle, self).event_collision(other, xdirection,
                                                   ydirection)


class Crusher(FallingObject, xsge_physics.MobileColliderWall,
              xsge_physics.Solid):

    nonstick_left = True
    nonstick_right = True
    nonstick_top = True
    nonstick_bottom = True
    sticky_top = True
    always_tangible = True
    burnable = True
    freezable = True
    gravity = 0
    fall_speed = CRUSHER_FALL_SPEED
    crushing = False

    def touch(self, other):
        other.hurt()

    def touch_death(self):
        pass

    def touch_hurt(self):
        pass

    def stop_up(self):
        self.yvelocity = 0
        self.crushing = False

    def stop_down(self):
        play_sound(brick_sound, self.x, self.y)
        self.yvelocity = 0
        self.gravity = 0
        sge.game.current_room.shake(CRUSHER_SHAKE_NUM)
        self.alarms["crush_end"] = CRUSHER_CRUSH_TIME

    def event_step(self, time_passed, delta_mult):
        if not self.crushing:
            super(Crusher, self).event_step(time_passed, delta_mult)
            if self.active:
                players = []
                crash_y = sge.game.current_room.height
                objects = (
                    sge.game.current_room.get_objects_at(
                        self.bbox_left - CRUSHER_LAX, self.bbox_bottom,
                        self.bbox_width + 2 * CRUSHER_LAX,
                        (sge.game.current_room.height - self.bbox_bottom +
                         sge.game.current_room.object_area_height)) |
                    sge.game.current_room.object_area_void)
                for obj in objects:
                    if (obj.bbox_top > self.bbox_bottom and
                            self.bbox_right > obj.bbox_left and
                            self.bbox_left < obj.bbox_right):
                        if isinstance(obj, xsge_physics.SolidTop):
                            crash_y = min(crash_y, obj.bbox_top)
                        elif isinstance(obj, xsge_physics.SlopeTopLeft):
                            crash_y = min(crash_y,
                                          obj.get_slope_y(self.bbox_right))
                        elif isinstance(obj, xsge_physics.SlopeTopRight):
                            crash_y = min(crash_y,
                                          obj.get_slope_y(self.bbox_left))
                    if (obj.bbox_top > self.bbox_bottom and
                            self.bbox_right + CRUSHER_LAX > obj.bbox_left and
                            self.bbox_left - CRUSHER_LAX < obj.bbox_right):
                        if isinstance(obj, Player):
                            players.append(obj)

                for player in players:
                    if player.bbox_top < crash_y + CRUSHER_LAX:
                        self.crushing = True
                        self.gravity = CRUSHER_GRAVITY
                        break
                else:
                    if not self.get_top_touching_wall():
                        self.yvelocity = -CRUSHER_RISE_SPEED
                        self.crushing = True

    def event_alarm(self, alarm_id):
        if alarm_id == "crush_end":
            self.yvelocity = -CRUSHER_RISE_SPEED

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, InteractiveObject) and other.knockable:
            other.knock(self)

        super(Crusher, self).event_collision(other, xdirection, ydirection)


class Krush(Crusher):

    def __init__(self, x, y, z=0, **kwargs):
        kwargs["sprite"] = krush_sprite
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)


class Krosh(Crusher):

    def __init__(self, x, y, z=0, **kwargs):
        kwargs["sprite"] = krosh_sprite
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)


class Circoflame(InteractiveObject):

    killed_by_void = False
    active_range = 0
    burnable = True
    freezable = True

    def __init__(self, center, x, y, z=0, **kwargs):
        self.center = weakref.ref(center)
        kwargs["sprite"] = circoflame_sprite
        kwargs["checks_collisions"] = False
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)

    def touch(self, other):
        other.hurt()

    def freeze(self):
        play_sound(sizzle_sound, self.x, self.y)
        center = self.center()
        if center is not None:
            center.destroy()
        self.destroy()

    def project_light(self):
        xsge_lighting.project_light(self.x, self.y, circoflame_light_sprite)


class CircoflameCenter(InteractiveObject):

    killed_by_void = False
    always_active = True
    never_tangible = True

    def __init__(self, x, y, z=0, radius=(TILE_SIZE * 4), pos=180,
                 rvelocity=2):
        self.radius = radius
        self.pos = pos
        self.rvelocity = rvelocity
        self.flame = Circoflame(self, x, y, z)
        super(CircoflameCenter, self).__init__(x, y, z, visible=False,
                                               tangible=False)

    def event_create(self):
        sge.game.current_room.add(self.flame)

    def event_step(self, time_passed, delta_mult):
        self.pos += self.rvelocity * delta_mult
        self.pos %= 360
        x = math.cos(math.radians(self.pos)) * self.radius
        y = math.sin(math.radians(self.pos)) * self.radius
        self.flame.x = self.x + x
        self.flame.y = self.y + y


class Boss(InteractiveObject):

    always_active = True
    always_tangible = True

    def __init__(self, x, y, ID="boss", death_timeline=None, stage=0,
                 **kwargs):
        self.ID = ID
        self.death_timeline = death_timeline
        self.stage = stage
        super(Boss, self).__init__(x, y, **kwargs)

    def event_create(self):
        super(Boss, self).event_create()
        sge.game.current_room.add_timeline_object(self)

    def event_destroy(self):
        for obj in sge.game.current_room.objects:
            if obj is not self and isinstance(obj, Boss) and obj.stage > 0:
                break
        else:
            if self.death_timeline:
                sge.game.current_room.load_timeline(self.death_timeline)
            else:
                sge.game.current_room.win_level(False)


class Snowman(FallingObject, Boss):

    burnable = True
    freezable = True
    knockable = True
    blastable = True

    def __init__(self, x, y, hp=SNOWMAN_HP, strong_stage=SNOWMAN_STRONG_STAGE,
                 final_stage=SNOWMAN_FINAL_STAGE, **kwargs):
        self.full_hp = hp
        self.hp = hp
        self.strong_stage = strong_stage
        self.final_stage = final_stage
        self.stunned = False
        self.stun_end = False
        self.stun_time = 0
        self.fixed_sprite = False
        kwargs["sprite"] = snowman_stand_sprite
        super(Snowman, self).__init__(x, y, **kwargs)

    def jump(self):
        if self.was_on_floor:
            play_sound(bigjump_sound, self.x, self.y)
            self.yvelocity = get_jump_speed(SNOWMAN_JUMP_HEIGHT, self.gravity)

    def stun(self):
        self.stunned = True
        self.fixed_sprite = True
        self.sprite = snowman_hurt_walk_sprite
        self.xvelocity = 0
        self.xacceleration = 0
        self.image_speed = 0
        if self.yvelocity < 0:
            self.yvelocity = 0
        self.alarms["stun_start"] = SNOWMAN_STOMP_DELAY

    def next_stage(self):
        self.xvelocity = 0
        self.xacceleration = 0
        if self.stage == self.final_stage:
            self.kill()
        else:
            if self.was_on_floor:
                play_sound(bigjump_sound, self.x, self.y)
                self.yvelocity = get_jump_speed(SNOWMAN_HOP_HEIGHT,
                                                self.gravity)
                self.stage += 1
                self.hp = self.full_hp
                self.stun_end = True
            else:
                self.alarms["stun"] = 1

    def kill(self):
        play_sound(fall_sound, self.x, self.y)
        DeadMan.create(self.x, self.y, self.z, sprite=self.sprite,
                       yvelocity=get_jump_speed(ENEMY_HIT_BELOW_HEIGHT),
                       image_xscale=self.image_xscale,
                       image_yscale=-abs(self.image_yscale))
        self.destroy()

    def move(self):
        super(Snowman, self).move()

        if "stomp_delay" not in self.alarms and not self.stunned:
            self.xacceleration = 0
            if self.stage > 0:
                if self.get_bottom_touching_wall():
                    can_jump = False
                    if self.stage >= self.final_stage:
                        walk_speed = SNOWMAN_FINAL_WALK_SPEED
                        accel = SNOWMAN_FINAL_ACCELERATION
                    elif self.stage >= self.strong_stage:
                        walk_speed = SNOWMAN_STRONG_WALK_SPEED
                        accel = SNOWMAN_STRONG_ACCELERATION
                        can_jump = True
                    else:
                        walk_speed = SNOWMAN_WALK_SPEED
                        accel = SNOWMAN_ACCELERATION

                    player = self.get_nearest_player()
                    if player is not None:
                        d = player.x - self.x
                        if (abs(self.xvelocity) < walk_speed or
                                (self.xvelocity > 0) != (d > 0)):
                            self.xacceleration = math.copysign(accel, d)
                        else:
                            self.xvelocity = math.copysign(walk_speed, d)

                        if (can_jump and self.yvelocity == 0 and
                                self.y - player.y >= SNOWMAN_JUMP_TRIGGER and
                                abs(self.xvelocity) >= walk_speed / 2):
                            self.jump()
            else:
                player = self.get_nearest_player()
                if player is not None:
                    self.image_xscale = math.copysign(self.image_xscale,
                                                      player.x - self.x)

    def stop_left(self):
        self.xvelocity = abs(self.xvelocity)

    def stop_right(self):
        self.xvelocity = -abs(self.xvelocity)

    def stop_up(self):
        self.yvelocity = 0

    def stop_down(self):
        if self.stage > 0 and self.yvelocity > 1:
            play_sound(brick_sound, self.x, self.y)
            self.yvelocity = 0
            self.xvelocity = 0
            self.xacceleration = 0
            sge.game.current_room.shake(SNOWMAN_SHAKE_NUM)
            self.alarms["stomp_delay"] = SNOWMAN_STOMP_DELAY
            if self.stun_end:
                self.fixed_sprite = False
                self.stunned = False
                self.stun_end = False

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.stomp_jump(self)
        if self.stage > 0 and not self.stunned:
            play_sound(squish_sound, self.x, self.y)
            self.stun()

    def burn(self):
        if self.stage > 0:
            play_sound(sizzle_sound, self.x, self.y)
            self.hp -= 1
            if self.hp <= 0:
                self.next_stage()

    def knock(self, other=None):
        if self.stage > 0 and not isinstance(other, (Icicle, FallingIcicle)):
            play_sound(stomp_sound, self.x, self.y)
            self.stun()

        if other is not None and other.knockable:
            other.knock(self)

    def blast(self):
        if self.stage > 0:
            play_sound(sizzle_sound, self.x, self.y)
            self.next_stage()

    def touch_hurt(self):
        pass

    def touch_death(self):
        self.kill()

    def event_step(self, time_passed, delta_mult):
        super(Snowman, self).event_step(time_passed, delta_mult)

        if not self.fixed_sprite:
            if self.was_on_floor:
                speed = abs(self.xvelocity)
                if speed > 0:
                    self.sprite = snowman_walk_sprite
                    self.image_speed = (speed * SNOWMAN_WALK_FRAMES_PER_PIXEL)
                else:
                    self.sprite = snowman_stand_sprite
            else:
                self.sprite = snowman_jump_sprite

        if self.xvelocity:
            self.image_xscale = math.copysign(self.image_xscale,
                                              self.xvelocity)

    def event_alarm(self, alarm_id):
        if alarm_id == "stun_start":
            self.image_speed = (SNOWMAN_STUNNED_WALK_SPEED *
                                SNOWMAN_WALK_FRAMES_PER_PIXEL)
            self.xvelocity = math.copysign(SNOWMAN_STUNNED_WALK_SPEED,
                                           self.image_xscale)
            self.alarms["stun"] = SNOWMAN_HITSTUN
        elif alarm_id == "stun":
            self.next_stage()


class Raccot(FallingObject, Boss):

    burnable = True
    freezable = True
    knockable = True
    blastable = True

    @property
    def stage(self):
        return self.__stage

    @stage.setter
    def stage(self, value):
        self.__stage = value
        if self.__ready:
            if value >= 2:
                self.alarms["hop"] = random.uniform(self.hop_interval_min,
                                                    self.hop_interval_max)
                self.alarms["charge"] = random.uniform(self.charge_interval_min,
                                                       self.charge_interval_max)
            else:
                if "hop" in self.alarms:
                    del self.alarms["hop"]
                if "charge" in self.alarms:
                    del self.alarms["charge"]
                if "charge_end" in self.alarms:
                    del self.alarms["charge_end"]

    def __init__(self, x, y, hp=RACCOT_HP, hop_time=RACCOT_HOP_TIME,
                 hop_interval_min=RACCOT_HOP_INTERVAL_MIN,
                 hop_interval_max=RACCOT_HOP_INTERVAL_MAX,
                 charge_interval_min=RACCOT_CHARGE_INTERVAL_MIN,
                 charge_interval_max=RACCOT_CHARGE_INTERVAL_MAX, **kwargs):
        self.hp = hp
        self.hop_time = hop_time
        self.hop_interval_min = hop_interval_min
        self.hop_interval_max = hop_interval_max
        self.charge_interval_min = charge_interval_min
        self.charge_interval_max = charge_interval_max
        self.direction = 0
        self.hopping = False
        self.charging = False
        self.crushing = False
        self.__ready = False
        kwargs["sprite"] = raccot_stand_sprite
        super(Raccot, self).__init__(x, y, **kwargs)
        self.__ready = True
        if self.stage >= 2:
            self.alarms["hop"] = random.uniform(self.hop_interval_min,
                                                self.hop_interval_max)
            self.alarms["charge"] = random.uniform(self.charge_interval_min,
                                                   self.charge_interval_max)

    def jump(self):
        if (self.was_on_floor and self.yvelocity == 0 and
                "stomp_delay" not in self.alarms):
            play_sound(bigjump_sound, self.x, self.y)
            self.yvelocity = get_jump_speed(RACCOT_JUMP_HEIGHT, self.gravity)

    def hop(self):
        if self.was_on_floor and self.yvelocity == 0:
            self.hopping = True
            self.xvelocity = 0
            self.sprite = raccot_stomp_sprite
            play_sound(yeti_gna_sound, self.x, self.y)

        self.alarms["do_hop"] = self.hop_time

    def do_hop(self):
        self.xvelocity = 0
        self.yvelocity = get_jump_speed(RACCOT_HOP_HEIGHT, self.gravity)
        self.sprite = raccot_hop_sprite
        if self.stage > 1:
            self.alarms["hop"] = random.uniform(self.hop_interval_min,
                                                self.hop_interval_max)

    def charge(self):
        self.charging = True
        self.alarms["charge_end"] = random.uniform(self.charge_interval_min,
                                                   self.charge_interval_max)

    def charge_end(self):
        self.charging = False
        if self.stage > 1:
            self.alarms["hop"] = random.uniform(self.hop_interval_min,
                                                self.hop_interval_max)
            self.alarms["charge"] = random.uniform(self.charge_interval_min,
                                                   self.charge_interval_max)

    def crush(self):
        self.crushing = True
        self.gravity = RACCOT_CRUSH_GRAVITY
        self.fall_speed = RACCOT_CRUSH_FALL_SPEED
        self.xacceleration = 0
        self.xvelocity = 0
        self.yvelocity = get_jump_speed(RACCOT_CRUSH_CHARGE, self.gravity)
        play_sound(yeti_gna_sound, self.x, self.y)

    def hurt(self):
        if self.stage > 0:
            play_sound(yeti_roar_sound, self.x, self.y)
            self.hp -= 1
            if self.hp <= 0:
                self.kill()

    def kill(self):
        play_sound(fall_sound, self.x, self.y)
        DeadMan.create(self.x, self.y, self.z, sprite=raccot_hop_sprite,
                       xvelocity=self.xvelocity,
                       yvelocity=get_jump_speed(ENEMY_HIT_BELOW_HEIGHT),
                       image_xscale=self.image_xscale,
                       image_yscale=-abs(self.image_yscale))
        self.destroy()

    def move(self):
        super(Raccot, self).move()
        player = self.get_nearest_player()
        if player is not None:
            if self.charging:
                self.direction = player.x - self.x
                if self.y - player.y >= RACCOT_JUMP_TRIGGER:
                    self.jump()
            elif self.stage > 1:
                self.direction = 0

            if not self.xvelocity:
                self.image_xscale = math.copysign(self.image_xscale,
                                                  player.x - self.x)

        if not self.crushing:
            if "stomp_delay" not in self.alarms:
                self.xacceleration = 0
                if self.direction and not self.hopping:
                    if (abs(self.xvelocity) < RACCOT_WALK_SPEED or
                            (self.xvelocity > 0) != (self.direction > 0)):
                        self.xacceleration = math.copysign(
                            RACCOT_ACCELERATION, self.direction)
                    else:
                        self.xvelocity = math.copysign(RACCOT_WALK_SPEED,
                                                       self.direction)

            if self.charging and not self.was_on_floor:
                players = []
                crash_y = sge.game.current_room.height
                objects = (
                    sge.game.current_room.get_objects_at(
                        self.bbox_left, self.bbox_bottom, self.bbox_width,
                        (sge.game.current_room.height - self.bbox_bottom +
                         sge.game.current_room.object_area_height)) |
                    sge.game.current_room.object_area_void)

                for obj in objects:
                    if (obj.bbox_top > self.bbox_bottom and
                            self.bbox_right > obj.bbox_left and
                            self.bbox_left < obj.bbox_right):
                        if isinstance(obj, xsge_physics.SolidTop):
                            crash_y = min(crash_y, obj.bbox_top)
                        elif isinstance(obj, xsge_physics.SlopeTopLeft):
                            crash_y = min(crash_y,
                                          obj.get_slope_y(self.bbox_right))
                        elif isinstance(obj, xsge_physics.SlopeTopRight):
                            crash_y = min(crash_y,
                                          obj.get_slope_y(self.bbox_left))
                    if (obj.bbox_top > self.bbox_bottom and
                            (self.bbox_right + RACCOT_CRUSH_LAX >
                             obj.bbox_left) and
                            (self.bbox_left - RACCOT_CRUSH_LAX <
                             obj.bbox_right)):
                        if isinstance(obj, Player):
                            players.append(obj)

                for player in players:
                    if player.bbox_top < crash_y:
                        self.crush()
                        break

    def stop_left(self):
        self.xvelocity = 0
        if self.charging:
            self.jump()

    def stop_right(self):
        self.xvelocity = 0
        if self.charging:
            self.jump()

    def stop_up(self):
        self.yvelocity = 0
        if self.get_bottom_touching_wall():
            self.stop_down()

    def stop_down(self):
        if self.stage > 0 and self.yvelocity >= RACCOT_STOMP_SPEED:
            crushed_brick = False
            self.xvelocity = 0
            self.xacceleration = 0
            sge.game.current_room.shake(RACCOT_SHAKE_NUM)
            self.alarms["stomp_delay"] = RACCOT_STOMP_DELAY

            if self.hopping:
                self.hopping = False
                for obj in sge.game.current_room.objects:
                    if isinstance(obj, RaccotIcicle):
                        obj.check_shake(True)

            if self.crushing and self.yvelocity >= RACCOT_CRUSH_SPEED:
                for obj in self.get_bottom_touching_wall():
                    if isinstance(obj, Brick):
                        obj.hit(self)
                        crushed_brick = True

                self.alarms["charge_end"] = 0

            self.yvelocity = 0
            if not crushed_brick:
                play_sound(brick_sound, self.x, self.y)

        self.hopping = False
        self.crushing = False
        self.gravity = self.__class__.gravity
        self.sprite = raccot_stand_sprite

    def touch(self, other):
        if self.stage > 0:
            other.hurt()

    def stomp(self, other):
        other.stomp_jump(self)

    def knock(self, other=None):
        if isinstance(other, InteractiveObject) and other.knockable:
            other.knock(self)

    def blast(self):
        self.hurt()

    def touch_hurt(self):
        pass

    def touch_death(self):
        self.kill()

    def event_step(self, time_passed, delta_mult):
        super(Raccot, self).event_step(time_passed, delta_mult)

        if self.was_on_floor or self.get_bottom_touching_wall():
            if self.hopping:
                self.sprite = raccot_stomp_sprite
            else:
                xm = (self.xvelocity > 0) - (self.xvelocity < 0)
                facing = (self.image_xscale > 0) - (self.image_xscale < 0)
                speed = abs(self.xvelocity)
                if speed > 0:
                    self.sprite = raccot_walk_sprite
                    self.image_speed = speed * RACCOT_WALK_FRAMES_PER_PIXEL
                    if xm != facing:
                        self.image_speed *= -1
                else:
                    self.sprite = raccot_stand_sprite
        else:
            if self.hopping:
                self.sprite = raccot_hop_sprite
            elif self.crushing:
                self.sprite = raccot_stomp_sprite
            else:
                self.sprite = raccot_jump_sprite

        if self.xvelocity:
            self.image_xscale = math.copysign(self.image_xscale,
                                              self.xvelocity)

    def event_alarm(self, alarm_id):
        if alarm_id == "hop":
            if not self.charging:
                self.hop()
        elif alarm_id == "do_hop":
            self.do_hop()
        elif alarm_id == "charge":
            if self.was_on_floor and "do_hop" not in self.alarms:
                self.charge()
            else:
                self.alarms["charge"] = 0
        elif alarm_id == "charge_end":
            self.charge_end()

    def event_destroy(self):
        super(Raccot, self).event_destroy()
        play_sound(yeti_roar_sound, self.x, self.y)


class FireFlower(FallingObject, WinPuffObject):

    fall_speed = FLOWER_FALL_SPEED
    slide_speed = 0
    win_puff_points = 0

    def __init__(self, x, y, z=0, **kwargs):
        kwargs["sprite"] = fire_flower_sprite
        x += fire_flower_sprite.origin_x
        y += fire_flower_sprite.origin_y
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)
        self.ammo = FIREBALL_AMMO
        self.light_sprite = fire_flower_light_sprite

    def touch(self, other):
        if other.pickup(self):
            self.gravity = 0

    def knock(self, other=None):
        self.yvelocity = get_jump_speed(ITEM_HIT_HEIGHT)

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None
            self.gravity = self.__class__.gravity

    def kick(self, up=False):
        if self.parent is not None:
            d = (self.image_xscale >= 0) - (self.image_xscale < 0)
            if self.ammo > 0:
                if up:
                    yv = get_jump_speed(FIREBALL_UP_HEIGHT, Fireball.gravity)
                else:
                    yv = FIREBALL_FALL_SPEED
                Fireball.create(self.x, self.y, self.parent.z,
                                sprite=fire_bullet_sprite,
                                xvelocity=(FIREBALL_SPEED * d), yvelocity=yv,
                                image_xscale=self.image_xscale)
                play_sound(shoot_sound, self.x, self.y)

                if not GOD:
                    self.ammo -= 1
                    self.sprite = fire_flower_sprite.copy()
                    lightness = int((self.ammo / FIREBALL_AMMO) * 255)
                    darkener = sge.gfx.Sprite(width=self.sprite.width,
                                              height=self.sprite.height)
                    darkener.draw_rectangle(0, 0, darkener.width, darkener.height,
                                            fill=sge.gfx.Color([lightness] * 3))
                    self.sprite.draw_sprite(darkener, 0, 0, 0,
                                            blend_mode=sge.BLEND_RGB_MULTIPLY)

                    self.light_sprite = fire_flower_light_sprite.copy()
                    darkener.width = self.light_sprite.width
                    darkener.height = self.light_sprite.height
                    self.light_sprite.draw_sprite(
                        darkener, 0, 0, 0, blend_mode=sge.BLEND_RGB_MULTIPLY)
            else:
                h = FLOWER_THROW_UP_HEIGHT if up else FLOWER_THROW_HEIGHT
                yv = get_jump_speed(h, ThrownFireFlower.gravity)
                self.parent.kick_object()
                play_sound(kick_sound, self.x, self.y)
                ThrownFireFlower.create(self.parent, self.x, self.y, self.z,
                                        sprite=self.sprite,
                                        xvelocity=(FIREBALL_SPEED * d),
                                        yvelocity=yv,
                                        image_xscale=self.image_xscale)
                self.parent = None
                self.destroy()
                pass

    def kick_up(self):
        self.kick(True)

    def project_light(self):
        if self.parent is not None:
            x = self.parent.x + self.image_origin_x
            y = self.parent.y
            if self.parent.image_xscale < 0:
                x -= self.sprite.width
        else:
            x = self.x
            y = self.y
        xsge_lighting.project_light(x, y, self.light_sprite)

    def win_puff(self):
        super(FireFlower, self).win_puff()
        sge.game.current_room.add_points(AMMO_POINTS * (self.ammo + 1))

    def event_end_step(self, time_passed, delta_mult):
        if self.parent is not None:
            direction = -1 if self.parent.image_xscale < 0 else 1
            self.image_xscale = abs(self.image_xscale) * direction


class IceFlower(FallingObject, WinPuffObject):

    fall_speed = FLOWER_FALL_SPEED
    slide_speed = 0
    win_puff_points = 0

    def __init__(self, x, y, z=0, **kwargs):
        kwargs["sprite"] = ice_flower_sprite
        x += ice_flower_sprite.origin_x
        y += ice_flower_sprite.origin_y
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)
        self.ammo = ICEBULLET_AMMO
        self.light_sprite = ice_flower_light_sprite

    def touch(self, other):
        if other.pickup(self):
            self.gravity = 0

    def knock(self, other=None):
        self.yvelocity = get_jump_speed(ITEM_HIT_HEIGHT)

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None
            self.gravity = self.__class__.gravity

    def kick(self):
        if self.parent is not None:
            d = (self.image_xscale >= 0) - (self.image_xscale < 0)
            if self.ammo > 0:
                if d < 0:
                    bbox_x = -ice_bullet_sprite.origin_x
                else:
                    bbox_x = (-ice_bullet_sprite.origin_x -
                              ice_bullet_sprite.bbox_width +
                              ice_bullet_sprite.width)
                    
                IceBullet.create(self.x, self.y, self.parent.z,
                                 sprite=ice_bullet_sprite,
                                 xvelocity=(ICEBULLET_SPEED * d),
                                 bbox_x=bbox_x)
                play_sound(shoot_sound, self.x, self.y)

                if not GOD:
                    self.ammo -= 1
                    self.sprite = ice_flower_sprite.copy()
                    lightness = int((self.ammo / ICEBULLET_AMMO) * 255)
                    darkener = sge.gfx.Sprite(width=self.sprite.width,
                                              height=self.sprite.height)
                    darkener.draw_rectangle(0, 0, darkener.width, darkener.height,
                                            fill=sge.gfx.Color([lightness] * 3))
                    self.sprite.draw_sprite(darkener, 0, 0, 0,
                                            blend_mode=sge.BLEND_RGB_MULTIPLY)

                    self.light_sprite = ice_flower_light_sprite.copy()
                    darkener.width = self.light_sprite.width
                    darkener.height = self.light_sprite.height
                    self.light_sprite.draw_sprite(
                        darkener, 0, 0, 0, blend_mode=sge.BLEND_RGB_MULTIPLY)
            else:
                yv = get_jump_speed(FLOWER_THROW_HEIGHT,
                                    ThrownIceFlower.gravity)
                self.parent.kick_object()
                play_sound(kick_sound, self.x, self.y)
                ThrownIceFlower.create(self.parent, self.x, self.y, self.z,
                                       sprite=self.sprite,
                                       xvelocity=(FIREBALL_SPEED * d),
                                       yvelocity=yv,
                                       image_xscale=self.image_xscale)
                self.parent = None
                self.destroy()
                pass

    def project_light(self):
        if self.parent is not None:
            x = self.parent.x + self.image_origin_x
            y = self.parent.y
            if self.parent.image_xscale < 0:
                x -= self.sprite.width
        else:
            x = self.x
            y = self.y
        xsge_lighting.project_light(x, y, self.light_sprite)

    def win_puff(self):
        super(IceFlower, self).win_puff()
        sge.game.current_room.add_points(AMMO_POINTS * (self.ammo + 1))

    def event_end_step(self, time_passed, delta_mult):
        if self.parent is not None:
            direction = -1 if self.parent.image_xscale < 0 else 1
            self.image_xscale = abs(self.image_xscale) * direction


class ThrownFlower(FallingObject, WinPuffObject):

    active_range = BULLET_ACTIVE_RANGE
    fall_speed = FLOWER_FALL_SPEED

    def __init__(self, thrower, *args, **kwargs):
        self.thrower = thrower
        super(ThrownFlower, self).__init__(*args, **kwargs)

    def dissipate(self):
        play_sound(stomp_sound, self.x, self.y)
        Smoke.create(self.x, self.y, self.z, sprite=smoke_puff_sprite)
        self.destroy()

    def deactivate(self):
        self.destroy()

    def touch_hurt(self):
        pass

    def touch_death(self):
        self.dissipate()

    def event_physics_collision_left(self, other, move_loss):
        self.event_collision(other, -1, 0)
        self.dissipate()

    def event_physics_collision_right(self, other, move_loss):
        self.event_collision(other, 1, 0)
        self.dissipate()

    def event_physics_collision_top(self, other, move_loss):
        self.event_collision(other, 0, -1)
        self.dissipate()

    def event_physics_collision_bottom(self, other, move_loss):
        self.event_collision(other, 0, 1)
        self.dissipate()


class ThrownFireFlower(ThrownFlower):

    def event_collision(self, other, xdirection, ydirection):
        if ((isinstance(other, InteractiveObject) and other.burnable) or
                isinstance(other, (Iceblock, ThinIce))):
            self.dissipate()
            other.burn()

        super(ThrownFlower, self).event_collision(other, xdirection, ydirection)


class ThrownIceFlower(ThrownFlower):

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, InteractiveObject) and other.burnable:
            self.dissipate()
            other.freeze()

        super(ThrownFlower, self).event_collision(other, xdirection, ydirection)


class Fireball(FallingObject):

    active_range = BULLET_ACTIVE_RANGE
    gravity = FIREBALL_GRAVITY
    fall_speed = FIREBALL_FALL_SPEED

    def deactivate(self):
        self.destroy()

    def dissipate(self):
        if self in sge.game.current_room.objects:
            Smoke.create(self.x, self.y, self.z, sprite=fireball_smoke_sprite)
            play_sound(fire_dissipate_sound, self.x, self.y)
            self.destroy()

    def touch_hurt(self):
        pass

    def touch_death(self):
        self.destroy()

    def project_light(self):
        xsge_lighting.project_light(self.x, self.y, fireball_light_sprite)

    def stop_left(self):
        self.dissipate()

    def stop_right(self):
        self.dissipate()

    def stop_down(self):
        self.yvelocity = get_jump_speed(FIREBALL_BOUNCE_HEIGHT, self.gravity)

    def event_collision(self, other, xdirection, ydirection):
        if ((isinstance(other, InteractiveObject) and other.burnable) or
                isinstance(other, (Iceblock, ThinIce))):
            other.burn()
            self.dissipate()

        super(Fireball, self).event_collision(other, xdirection, ydirection)

    def event_physics_collision_left(self, other, move_loss):
        super(Fireball, self).event_physics_collision_left(other, move_loss)
        self.event_collision(other, -1, 0)

    def event_physics_collision_right(self, other, move_loss):
        super(Fireball, self).event_physics_collision_right(other, move_loss)
        self.event_collision(other, 1, 0)

    def event_physics_collision_top(self, other, move_loss):
        super(Fireball, self).event_physics_collision_top(other, move_loss)
        self.event_collision(other, 0, -1)

    def event_physics_collision_bottom(self, other, move_loss):
        super(Fireball, self).event_physics_collision_bottom(other, move_loss)
        self.event_collision(other, 0, 1)


class IceBullet(InteractiveObject, xsge_physics.Collider):

    active_range = BULLET_ACTIVE_RANGE

    def deactivate(self):
        self.destroy()

    def dissipate(self):
        if self in sge.game.current_room.objects:
            Smoke.create(self.x, self.y, self.z,
                         sprite=ice_bullet_break_sprite)
            play_sound(icebullet_break_sound, self.x, self.y)
            self.destroy()

    def event_collision(self, other, xdirection, ydirection):
        if ((isinstance(other, InteractiveObject) and other.freezable) or
                isinstance(other, ThinIce)):
            other.freeze()
            self.dissipate()

        super(IceBullet, self).event_collision(other, xdirection, ydirection)

    def event_physics_collision_left(self, other, move_loss):
        self.event_collision(other, -1, 0)
        self.dissipate()

    def event_physics_collision_right(self, other, move_loss):
        self.event_collision(other, 1, 0)
        self.dissipate()

    def event_physics_collision_top(self, other, move_loss):
        self.event_collision(other, 0, -1)
        self.dissipate()

    def event_physics_collision_bottom(self, other, move_loss):
        self.event_collision(other, 0, 1)
        self.dissipate()


class TuxDoll(FallingObject):

    fall_speed = FLOWER_FALL_SPEED
    slide_speed = 0

    def __init__(self, x, y, z=0, **kwargs):
        kwargs["sprite"] = tuxdoll_sprite
        x += tuxdoll_sprite.origin_x
        y += tuxdoll_sprite.origin_y
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)

    def touch(self, other):
        play_sound(tuxdoll_sound, self.x, self.y)
        sge.game.current_room.add_points(TUXDOLL_POINTS)
        if main_area and main_area not in tuxdolls_found:
            tuxdolls_found.append(main_area)

        self.destroy()

    def knock(self, other=None):
        self.yvelocity = get_jump_speed(ITEM_HIT_HEIGHT)


class RockWall(xsge_physics.MobileWall, xsge_physics.Solid):

    push_left = False
    push_right = False
    push_down = False
    sticky_top = True

    def __init__(self, x, y, z=0, parent=None, **kwargs):
        if parent is not None:
            self.parent = weakref.ref(parent)
        else:
            self.parent = lambda: None
        super(RockWall, self).__init__(x, y, z, **kwargs)


class Rock(FallingObject, CrowdBlockingObject, WinPuffObject):

    active_range = ROCK_ACTIVE_RANGE
    gravity = ROCK_GRAVITY
    fall_speed = ROCK_FALL_SPEED
    win_puff_score = 0

    def __init__(self, x, y, z=0, **kwargs):
        kwargs.setdefault("sprite", rock_sprite)
        kwargs["checks_collisions"] = False
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)
        self.wall = RockWall(
            self.x, self.y, self.z, parent=self, sprite=self.sprite,
            visible=False, active=False, checks_collisions=False,
            image_xscale=self.image_xscale, image_yscale=self.image_yscale)

    def move_x(self, move, absolute=False, do_events=True, exclude_events=()):
        super(Rock, self).move_x(move, absolute=absolute, do_events=do_events,
                                 exclude_events=exclude_events)
        tangible = self.tangible
        self.tangible = False
        self.wall.move_x(self.x - self.wall.x)
        self.tangible = tangible
        self.x = self.wall.x

    def move_y(self, move, absolute=False, do_events=True, exclude_events=()):
        super(Rock, self).move_y(move, absolute=absolute, do_events=do_events,
                                 exclude_events=exclude_events)
        tangible = self.tangible
        self.tangible = False
        self.wall.move_y(self.y - self.wall.y)
        self.tangible = tangible
        self.y = self.wall.y

    def touch(self, other):
        if other.pickup(self):
            self.active = False
            self.wall.tangible = False
            self.xvelocity = 0
            self.yvelocity = 0
            if other.action_pressed:
                other.action()

    def stop_left(self):
        self.xvelocity = 0

    def stop_right(self):
        self.xvelocity = 0

    def stop_up(self):
        self.yvelocity = 0

    def touch_hurt(self):
        pass

    def touch_death(self):
        pass

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.active = True
            self.wall.tangible = True
            self.parent = None

    def kick(self):
        if self.parent is not None:
            self.parent.kick_object()
            self.active = True
            self.wall.tangible = True
            self.xvelocity = math.copysign(KICK_FORWARD_SPEED,
                                           self.parent.image_xscale)
            self.yvelocity = get_jump_speed(KICK_FORWARD_HEIGHT, Rock.gravity)
            self.parent = None

    def kick_up(self):
        if self.parent is not None:
            self.parent.kick_object()
            self.active = True
            self.wall.tangible = True
            self.xvelocity = self.parent.xvelocity
            self.yvelocity = get_jump_speed(KICK_UP_HEIGHT, Rock.gravity)
            self.parent = None

    def event_create(self):
        super(Rock, self).event_create()
        sge.game.current_room.add(self.wall)

    def event_end_step(self, time_passed, delta_mult):
        if (self.yvelocity >= 0 and
                (self.get_bottom_touching_wall() or
                 self.get_bottom_touching_slope())):
            self.xdeceleration = ROCK_FRICTION
        else:
            self.xdeceleration = 0

    def event_destroy(self):
        if self.wall is not None:
            self.wall.destroy()


class FixedSpring(FallingObject):

    active_range = ROCK_ACTIVE_RANGE
    gravity = ROCK_GRAVITY
    fall_speed = ROCK_FALL_SPEED
    jump_height = SPRING_JUMP_HEIGHT

    def set_sprite(self):
        # This is a function because the names referenced don't exist
        # when this class is defined, and these therefore can't be class
        # attributes.
        self.normal_sprite = fixed_spring_sprite
        self.expand_sprite = fixed_spring_expand_sprite

    def set_sound(self):
        self.sound = spring_sound

    def __init__(self, x, y, z=0, **kwargs):
        self.set_sprite()
        self.set_sound()
        kwargs["sprite"] = self.normal_sprite
        x += self.normal_sprite.origin_x
        y += self.normal_sprite.origin_y
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)

    def stomp(self, other):
        if other is not self.parent and other.yvelocity > 0:
            other.stomp_jump(self, self.jump_height)
            play_sound(self.sound, self.x, self.y)
            self.sprite = self.expand_sprite
            self.image_index = 0
            self.image_fps = None

    def touch_hurt(self):
        pass

    def event_animation_end(self):
        if self.sprite == self.expand_sprite:
            self.sprite = self.normal_sprite


class Spring(FixedSpring, WinPuffObject):

    active_range = ROCK_ACTIVE_RANGE
    gravity = ROCK_GRAVITY
    fall_speed = ROCK_FALL_SPEED
    win_puff_score = 0

    def set_sprite(self):
        self.normal_sprite = spring_sprite
        self.expand_sprite = spring_expand_sprite

    def touch(self, other):
        if other.pickup(self):
            self.gravity = 0
            if other.action_pressed:
                other.action()

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None
            self.gravity = self.__class__.gravity

    def kick(self):
        if self.parent is not None:
            self.parent.kick_object()
            self.xvelocity = math.copysign(KICK_FORWARD_SPEED,
                                           self.parent.image_xscale)
            self.yvelocity = get_jump_speed(KICK_FORWARD_HEIGHT, Rock.gravity)
            self.gravity = self.__class__.gravity
            self.parent = None

    def kick_up(self):
        if self.parent is not None:
            self.parent.kick_object()
            self.xvelocity = self.parent.xvelocity
            self.yvelocity = get_jump_speed(KICK_UP_HEIGHT, Rock.gravity)
            self.gravity = self.__class__.gravity
            self.parent = None

    def event_end_step(self, time_passed, delta_mult):
        if (self.yvelocity >= 0 and
                (self.get_bottom_touching_wall() or
                 self.get_bottom_touching_slope())):
            self.xdeceleration = ROCK_FRICTION
        else:
            self.xdeceleration = 0


class RustySpring(Spring):

    def set_sprite(self):
        self.normal_sprite = rusty_spring_sprite
        self.expand_sprite = rusty_spring_expand_sprite

    def set_sound(self):
        self.sound = rusty_spring_sound

    def event_animation_end(self):
        if self.sprite == self.expand_sprite:
            Corpse.create(self.x, self.y, self.z,
                          sprite=rusty_spring_dead_sprite,
                          image_xscale=self.image_xscale,
                          image_yscale=self.image_yscale)
            self.destroy()


class Lantern(FallingObject):

    active_range = ROCK_ACTIVE_RANGE
    gravity = ROCK_GRAVITY
    fall_speed = ROCK_FALL_SPEED

    def __init__(self, x, y, color="white", **kwargs):
        kwargs["sprite"] = lantern_sprite
        sge.dsp.Object.__init__(self, x, y, **kwargs)

        c = sge.gfx.Color(color)
        if c.red < 255 or c.green < 255 or c.blue < 255:
            self.light_sprite = light_sprite.copy()
            blender = sge.gfx.Sprite(width=self.light_sprite.width,
                                     height=self.light_sprite.height)
            blender.draw_rectangle(0, 0, blender.width, blender.height, fill=c)
            self.light_sprite.draw_sprite(blender, 0, 0, 0,
                                          blend_mode=sge.BLEND_RGB_MULTIPLY)
        else:
            self.light_sprite = light_sprite

    def touch(self, other):
        if other.pickup(self):
            self.gravity = 0
            if other.action_pressed:
                other.action()

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None
            self.gravity = self.__class__.gravity

    def kick(self):
        if self.parent is not None:
            self.parent.kick_object()
            self.xvelocity = math.copysign(KICK_FORWARD_SPEED,
                                           self.parent.image_xscale)
            self.yvelocity = get_jump_speed(KICK_FORWARD_HEIGHT, Rock.gravity)
            self.gravity = self.__class__.gravity
            self.parent = None

    def kick_up(self):
        if self.parent is not None:
            self.parent.kick_object()
            self.xvelocity = self.parent.xvelocity
            self.yvelocity = get_jump_speed(KICK_UP_HEIGHT, Rock.gravity)
            self.gravity = self.__class__.gravity
            self.parent = None

    def project_light(self):
        if self.parent is not None:
            x = self.parent.x + self.image_origin_x
            y = self.parent.y
            if self.parent.image_xscale < 0:
                x -= self.sprite.width
        else:
            x = self.x
            y = self.y
        xsge_lighting.project_light(x, y, self.light_sprite)

    def event_end_step(self, time_passed, delta_mult):
        if (self.yvelocity >= 0 and
                (self.get_bottom_touching_wall() or
                 self.get_bottom_touching_slope())):
            self.xdeceleration = ROCK_FRICTION
        else:
            self.xdeceleration = 0


class TimelineSwitcher(InteractiveObject):

    def __init__(self, x, y, timeline=None, **kwargs):
        self.timeline = timeline
        kwargs["visible"] = False
        kwargs["checks_collisions"] = False
        sge.dsp.Object.__init__(self, x, y, **kwargs)

    def touch(self, other):
        sge.game.current_room.load_timeline(self.timeline)
        self.destroy()


class Iceblock(xsge_physics.Solid):

    def __init__(self, x, y, **kwargs):
        kwargs["checks_collisions"] = False
        sge.dsp.Object.__init__(self, x, y, **kwargs)

    def burn(self):
        play_sound(sizzle_sound, self.x, self.y)
        Smoke.create(self.x, self.y, self.z, sprite=iceblock_melt_sprite)
        self.destroy()


class BossBlock(InteractiveObject):

    never_active = True
    never_tangible = True

    def __init__(self, x, y, ID=None, **kwargs):
        self.ID = ID
        kwargs["visible"] = False
        sge.dsp.Object.__init__(self, x, y, **kwargs)

    def event_create(self):
        super(BossBlock, self).event_create()
        sge.game.current_room.add_timeline_object(self)

    def activate(self):
        self.child = xsge_physics.Solid.create(
            self.x, self.y, self.z, sprite=boss_block_sprite)
        self.child.x += self.child.image_origin_x
        self.child.y += self.child.image_origin_y
        Smoke.create(self.child.x, self.child.y, z=(self.child.z + 0.5),
                     sprite=item_spawn_cloud_sprite)
        play_sound(pop_sound, self.x, self.y)

    def deactivate(self):
        if self.child is not None:
            Smoke.create(self.child.x, self.child.y, z=self.child.z,
                         sprite=smoke_plume_sprite)
            self.child.destroy()
            self.child = None
            play_sound(pop_sound, self.x, self.y)

    def update_active(self):
        pass


class HittableBlock(sge.dsp.Object):

    hit_sprite = None
    hit_obj = None

    def __init__(self, x, y, **kwargs):
        kwargs["checks_collisions"] = False
        sge.dsp.Object.__init__(self, x, y, **kwargs)

    def event_destroy(self):
        if self.hit_obj is not None:
            self.hit_obj.destroy()

    def event_begin_step(self, time_passed, delta_mult):
        if self.hit_obj is not None:
            if self.hit_obj.y > self.y:
                self.hit_obj.destroy()
                self.hit_obj = None
                self.visible = True
                self.event_hit_end()

    def hit(self, other):
        play_sound(brick_sound, self.x, self.y)
        if self.hit_obj is not None:
            self.hit_obj.destroy()
            self.hit_obj = None
            self.visible = True
            self.event_hit_end()

        if isinstance(self, xsge_physics.SolidTop):
            for obj in self.collision(InteractiveObject, y=(self.y - 1)):
                if obj.knockable:
                    obj.knock()

        if self in sge.game.current_room.objects:
            if self.hit_sprite is not None:
                s = self.hit_sprite
            else:
                s = self.sprite

            self.visible = False
            self.hit_obj = sge.dsp.Object.create(
                self.x, self.y, self.z, sprite=s, tangible=False,
                yvelocity=get_jump_speed(BLOCK_HIT_HEIGHT),
                yacceleration=GRAVITY, image_index=self.image_index,
                image_origin_x=self.image_origin_x,
                image_origin_y=self.image_origin_y,
                image_fps=self.image_fps, image_xscale=self.image_xscale,
                image_yscale=self.image_yscale,
                image_rotation=self.image_rotation)

            self.event_hit(other)

    def event_hit(self, other):
        pass

    def event_hit_end(self):
        pass


class Brick(HittableBlock, xsge_physics.Solid):

    def event_hit(self, other):
        for i in six.moves.range(BRICK_SHARD_NUM):
            xv = random.uniform(-BRICK_SHARD_SPEED, BRICK_SHARD_SPEED)
            yv = get_jump_speed(BRICK_SHARD_HEIGHT, BRICK_SHARD_GRAVITY)
            shard = DeadMan.create(
                self.x, self.y, self.z, sprite=brick_shard_sprite,
                xvelocity=xv, yvelocity=yv)
            shard.gravity = BRICK_SHARD_GRAVITY
            shard.fall_speed = BRICK_SHARD_FALL_SPEED

        sge.game.current_room.add_points(10)
        self.destroy()


class CoinBrick(Brick):

    coins = COINBRICK_COINS

    def __init__(self, x, y, disguised=False, **kwargs):
        if not disguised:
            kwargs["sprite"] = brick_sprite
        elif kwargs.get("sprite") is None:
            kwargs["bbox_x"] = brick_sprite.bbox_x
            kwargs["bbox_y"] = brick_sprite.bbox_y
            kwargs["bbox_width"] = brick_sprite.bbox_width
            kwargs["bbox_height"] = brick_sprite.bbox_height
        kwargs["checks_collisions"] = False
        sge.dsp.Object.__init__(self, x, y, **kwargs)

    def event_alarm(self, alarm_id):
        if alarm_id == "decay":
            self.coins -= 1
            self.alarms["decay"] = COINBRICK_DECAY_TIME

    def event_hit(self, other):
        if self.coins > 0:
            self.coins -= 1
            CoinCollect.create(self.x, self.y, z=(self.z + 0.5))
            if other is not None:
                other.coins += 1

            if "decay" not in self.alarms:
                self.alarms["decay"] = COINBRICK_DECAY_TIME
        else:
            super(CoinBrick, self).event_hit(other)


class EmptyBlock(HittableBlock, xsge_physics.Solid):

    pass


class ItemBlock(HittableBlock, xsge_physics.Solid):

    def __init__(self, x, y, item=None, disguised=False, **kwargs):
        if not disguised:
            kwargs["sprite"] = bonus_full_sprite
        elif kwargs.get("sprite") is None:
            kwargs["bbox_x"] = bonus_full_sprite.bbox_x
            kwargs["bbox_y"] = bonus_full_sprite.bbox_y
            kwargs["bbox_width"] = bonus_full_sprite.bbox_width
            kwargs["bbox_height"] = bonus_full_sprite.bbox_height
        kwargs["checks_collisions"] = False
        sge.dsp.Object.__init__(self, x, y, **kwargs)
        self.hit_sprite = bonus_empty_sprite
        self.item = item

    def event_hit(self, other):
        if self.item and self.item in TYPES:
            obj = TYPES[self.item].create(self.x, self.y, z=self.z)
            if obj.sprite is not None and self.sprite is not None:
                obj.x = (self.bbox_left + self.sprite.width / 2 +
                         obj.image_origin_x - obj.sprite.width / 2)
            else:
                obj.bbox_left = self.bbox_left
            obj.bbox_bottom = self.bbox_top
            Smoke.create(obj.x, obj.y, z=(obj.z + 0.5),
                         sprite=item_spawn_cloud_sprite)
            play_sound(find_powerup_sound, self.x, self.y)
        else:
            CoinCollect.create(self.x, self.y, z=(self.z + 0.5))
            if other is not None:
                other.coins += 1

    def event_hit_end(self):
        EmptyBlock.create(self.x, self.y, z=self.z, sprite=bonus_empty_sprite)
        self.destroy()


class HiddenItemBlock(HittableBlock):

    def __init__(self, x, y, item=None, **kwargs):
        kwargs["sprite"] = None
        kwargs["bbox_x"] = bonus_full_sprite.bbox_x
        kwargs["bbox_y"] = bonus_full_sprite.bbox_y
        kwargs["bbox_width"] = bonus_full_sprite.bbox_width
        kwargs["bbox_height"] = bonus_full_sprite.bbox_height
        kwargs["checks_collisions"] = False
        sge.dsp.Object.__init__(self, x, y, **kwargs)
        self.item = item

    def hit(self, other):
        ib = ItemBlock.create(self.x, self.y, item=self.item, z=self.z)
        ib.hit(other)
        self.destroy()


class InfoBlock(HittableBlock, xsge_physics.Solid):

    def __init__(self, x, y, text="(null)", **kwargs):
        super(InfoBlock, self).__init__(x, y, **kwargs)
        self.text = text.replace("\\n", "\n")

    def event_hit_end(self):
        DialogBox(gui_handler, _(self.text), self.sprite).show()


class ThinIce(xsge_physics.Solid):

    def __init__(self, x, y, z=0, permanent=False, **kwargs):
        kwargs["sprite"] = thin_ice_sprite
        kwargs["checks_collisions"] = False
        kwargs["image_fps"] = 0
        sge.dsp.Object.__init__(self, x, y, z, **kwargs)
        self.permanent = permanent
        self.crack_time = 0
        self.freeze_time = 0

    def burn(self):
        self.crack()

    def freeze(self):
        if self.image_index > 0:
            self.image_index -= 1

    def event_step(self, time_passed, delta_mult):
        if self.sprite is thin_ice_sprite:
            players = self.collision(Player, y=(self.y - 1))
            if players:
                if not GOD:
                    for player in players:
                        self.crack_time += delta_mult
                        while self.crack_time >= ICE_CRACK_TIME:
                            self.crack_time -= ICE_CRACK_TIME
                            self.crack()
            elif not self.permanent:
                if self.image_index > 0:
                    rfa = delta_mult * ICE_REFREEZE_RATE
                    self.crack_time -= rfa
                    self.rfa = max(0, -self.crack_time)
                    self.crack_time = max(0, self.crack_time)
                    self.freeze_time += rfa
                    while self.freeze_time >= ICE_CRACK_TIME:
                        self.freeze_time -= ICE_CRACK_TIME
                        if self.image_index > 0:
                            self.image_index -= 1
                else:
                    self.crack_time -= delta_mult * ICE_REFREEZE_RATE
                    self.crack_time = max(0, self.crack_time)

    def event_animation_end(self):
        self.destroy()

    def shatter(self):
        if self.sprite != thin_ice_break_sprite:
            self.sprite = thin_ice_break_sprite
            self.image_index = 0
            self.image_fps = None
            play_sound(ice_shatter_sound, self.x, self.y)

    def crack(self):
        if self.image_index + 1 < self.sprite.frames:
            play_sound(random.choice(ice_crack_sounds), self.x, self.y)
            self.image_index += 1
            self.freeze_time = 0
        else:
            self.shatter()


class Lava(xsge_tmx.Decoration):

    def event_create(self):
        self.sprite = lava_body_sprite


class LavaSurface(xsge_tmx.Decoration):

    def event_create(self):
        self.sprite = lava_surface_sprite


class Goal(xsge_tmx.Decoration):

    def event_create(self):
        self.sprite = goal_sprite


class GoalTop(xsge_tmx.Decoration):

    def event_create(self):
        self.sprite = goal_top_sprite


class Coin(sge.dsp.Object):

    def __init__(self, x, y, **kwargs):
        kwargs["sprite"] = coin_sprite
        kwargs["checks_collisions"] = False
        super(Coin, self).__init__(x, y, **kwargs)

    def event_step(self, time_passed, delta_mult):
        self.image_index = coin_animation.image_index

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, Player) and self in sge.game.current_room.objects:
            CoinCollect.create(self.x, self.y, z=self.z,
                               image_index=self.image_index)
            self.destroy()
            other.coins += 1


class CoinCollect(sge.dsp.Object):

    def __init__(self, x, y, **kwargs):
        kwargs["sprite"] = coin_sprite
        kwargs["tangible"] = False
        sge.dsp.Object.__init__(self, x, y, **kwargs)

    def event_create(self):
        play_sound(coin_sound, self.x, self.y)
        sge.game.current_room.add_points(COIN_POINTS)
        self.alarms["destroy"] = COIN_COLLECT_TIME
        self.yvelocity = -COIN_COLLECT_SPEED

    def event_step(self, time_passed, delta_mult):
        T = self.alarms.get("destroy", COIN_COLLECT_TIME)
        self.image_alpha = 255 * (T / COIN_COLLECT_TIME)

    def event_alarm(self, alarm_id):
        if alarm_id == "destroy":
            self.destroy()


class Spawn(sge.dsp.Object):

    def __init__(self, x, y, spawn_id=None, **kwargs):
        kwargs["visible"] = False
        kwargs["tangible"] = False
        super(Spawn, self).__init__(x, y, **kwargs)
        self.spawn_id = spawn_id


class Checkpoint(InteractiveObject):

    def __init__(self, x, y, dest=None, **kwargs):
        kwargs["visible"] = False
        super(Checkpoint, self).__init__(x, y, **kwargs)
        self.dest = dest

    def event_create(self):
        if self.dest is not None:
            if ":" not in self.dest:
                self.dest = "{}:{}".format(sge.game.current_room.fname,
                                           self.dest)
        self.reset()

    def reset(self):
        pass

    def touch(self, other):
        global current_checkpoints
        current_checkpoints[main_area] = self.dest

        for obj in sge.game.current_room.objects:
            if isinstance(obj, Checkpoint):
                obj.reset()


class Bell(Checkpoint):

    def __init__(self, x, y, dest=None, **kwargs):
        kwargs["sprite"] = bell_sprite
        InteractiveObject.__init__(self, x, y, **kwargs)
        self.dest = dest

    def reset(self):
        if current_checkpoints.get(main_area) == self.dest:
            self.image_fps = None
        else:
            self.image_fps = 0
            self.image_index = 0

    def touch(self, other):
        super(Bell, self).touch(other)
        play_sound(bell_sound, self.x, self.y)


class Door(sge.dsp.Object):

    def __init__(self, x, y, dest=None, spawn_id=None, **kwargs):
        y += 64
        kwargs["sprite"] = door_sprite
        kwargs["checks_collisions"] = False
        kwargs["image_fps"] = 0
        super(Door, self).__init__(x, y, **kwargs)
        self.dest = dest
        self.spawn_id = spawn_id
        self.occupant = None

    def warp(self, other):
        if self.occupant is None and self.image_index == 0:
            self.occupant = other
            play_sound(door_sound, self.x, self.y)
            self.image_fps = self.sprite.fps

            other.visible = False
            other.tangible = False
            other.warping = True
            other.xvelocity = 0
            other.yvelocity = 0
            other.xacceleration = 0
            other.yacceleration = 0
            other.xdeceleration = 0
            other.ydeceleration = 0

    def warp_end(self):
        warp(self.dest)

    def event_step(self, time_passed, delta_mult):
        if self.occupant is not None:
            s = get_scaled_copy(self.occupant)
            if self.image_fps > 0:
                sge.game.current_room.project_sprite(
                    door_back_sprite, 0, self.x, self.y, self.z - 0.5)
                sge.game.current_room.project_sprite(s, 0, self.x, self.y,
                                                     self.occupant.z)
            else:
                dbs = door_back_sprite.copy()
                dbs.draw_sprite(s, 0, dbs.origin_x, dbs.origin_y)
                sge.game.current_room.project_sprite(dbs, 0, self.x, self.y,
                                                     self.z - 0.5)
        elif self.image_index != 0:
            sge.game.current_room.project_sprite(door_back_sprite, 0, self.x,
                                                 self.y, self.z - 0.5)

    def event_animation_end(self):
        if self.image_fps > 0:
            if self.dest and (':' in self.dest or self.dest == "__map__"):
                self.image_fps = -self.image_fps
                self.image_index = self.sprite.frames - 1
            else:
                self.image_fps = 0
                self.image_index = self.sprite.frames - 1
                self.occupant.visible = True
                self.occupant.tangible = True
                self.occupant.warping = False
                self.occupant.xvelocity = 0
                self.occupant.yvelocity = 0
                self.occupant = None
        elif self.image_fps < 0:
            play_sound(door_shut_sound, self.x, self.y)
            self.image_fps = 0
            self.image_index = 0
            self.occupant = None
            self.warp_end()


class WarpSpawn(xsge_path.Path):

    silent = False

    def __init__(self, x, y, points=(), dest=None, spawn_id=None, **kwargs):
        super(WarpSpawn, self).__init__(x, y, points=points, **kwargs)
        self.dest = dest
        self.spawn_id = spawn_id
        self.direction = None
        self.end_direction = None
        self.warps_out = []

        if points:
            xm, ym = points[0]
            if abs(xm) > abs(ym):
                self.direction = "right" if xm > 0 else "left"
            elif ym:
                self.direction = "down" if ym > 0 else "up"
            else:
                warnings.warn("Warp at position ({}, {}) has no direction".format(x, y))

            if len(points) >= 2:
                x1, y1 = points[-2]
                x2, y2 = points[-1]
                xm = x2 - x1
                ym = y2 - y1
                if abs(xm) > abs(ym):
                    self.end_direction = "right" if xm > 0 else "left"
                elif ym:
                    self.end_direction = "down" if ym > 0 else "up"
                else:
                    warnings.warn("Warp at position ({}, {}) has no end direction".format(x, y))
            else:
                self.end_direction = self.direction

    def event_step(self, time_passed, delta_mult):
        super(WarpSpawn, self).event_step(time_passed, delta_mult)

        x, y = self.points[-1]
        x += self.x
        y += self.y
        finished = []
        for obj in self.warps_out:
            left_edge = obj.x - obj.image_origin_x
            top_edge = obj.y - obj.image_origin_y
            if self.end_direction == "left":
                if obj.bbox_right <= x:
                    obj.bbox_right = x
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(
                        math.ceil(x - left_edge), 0, warp_sprite.width,
                        warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, self.z)
            elif self.end_direction == "right":
                if obj.bbox_left >= x:
                    obj.bbox_left = x
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(0, 0, math.floor(x - left_edge),
                                           warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, self.z)
            elif self.end_direction == "up":
                if obj.bbox_bottom <= y:
                    obj.bbox_bottom = y
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(
                        0, math.ceil(y - top_edge), warp_sprite.width,
                        warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, self.z)
            elif self.end_direction == "down":
                if obj.bbox_top >= y:
                    obj.bbox_top = y
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(0, 0, warp_sprite.width,
                                           math.floor(y - top_edge))
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, self.z)

        for obj in finished:
            obj.visible = True
            obj.tangible = True
            obj.warping = False
            obj.speed = 0
            self.warps_out.remove(obj)

    def event_follow_end(self, obj):
        global level_timers
        global score

        if self.dest and (':' in self.dest or self.dest == "__map__"):
            warp(self.dest)
        else:
            if not self.silent:
                play_sound(pipe_sound, obj.x, obj.y)

            self.warps_out.append(obj)
            x, y = self.points[-1]
            x += self.x
            y += self.y
            if self.end_direction == "left":
                obj.x = x + obj.sprite.origin_x
                obj.y = y
                obj.move_direction = 180
            elif self.end_direction == "right":
                obj.x = x + obj.sprite.origin_x - obj.sprite.width
                obj.y = y
                obj.move_direction = 0
            elif self.end_direction == "up":
                obj.x = x
                obj.y = y + obj.sprite.origin_y
                obj.move_direction = 270
            elif self.end_direction == "down":
                obj.x = x
                obj.y = y + obj.sprite.origin_y - obj.sprite.height
                obj.move_direction = 90

            obj.speed = WARP_SPEED
            obj.xacceleration = 0
            obj.yacceleration = 0
            obj.xdeceleration = 0
            obj.ydeceleration = 0


class Warp(WarpSpawn):

    def __init__(self, x, y, **kwargs):
        super(Warp, self).__init__(x, y, **kwargs)
        self.warps_in = []

    def warp(self, other):
        if not self.silent:
            play_sound(pipe_sound, other.x, other.y)

        self.warps_in.append(other)

        if getattr(other, "held_object") is not None:
            other.held_object.drop()

        other.visible = False
        other.tangible = False
        other.warping = True
        other.move_direction = {"right": 0, "up": 270, "left": 180,
                                "down": 90}.get(self.direction, 0)
        other.speed = WARP_SPEED
        other.xacceleration = 0
        other.yacceleration = 0
        other.xdeceleration = 0
        other.ydeceleration = 0

    def event_create(self):
        if self not in sge.game.current_room.warps:
            sge.game.current_room.warps.append(self)

    def event_end_step(self, time_passed, delta_mult):
        super(Warp, self).event_step(time_passed, delta_mult)

        finished = []
        for obj in self.warps_in:
            left_edge = obj.x - obj.image_origin_x
            top_edge = obj.y - obj.image_origin_y
            if self.direction == "left":
                if obj.x <= self.x + obj.image_origin_x - obj.sprite.width:
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(
                        0, 0, math.floor(self.x - left_edge),
                        warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, self.z)
            elif self.direction == "right":
                if obj.x >= self.x + obj.image_origin_x:
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(
                        math.ceil(self.x - left_edge), 0, warp_sprite.width,
                        warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, self.z)
            elif self.direction == "up":
                if obj.y <= self.y + obj.image_origin_y - obj.sprite.height:
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(0, 0, warp_sprite.width,
                                           math.floor(self.y - top_edge))
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, self.z)
            elif self.direction == "down":
                if obj.y >= self.y + obj.image_origin_y:
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(
                        0, math.ceil(self.y - top_edge), warp_sprite.width,
                        warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, self.z)

        for obj in finished:
            obj.x = self.x
            obj.y = self.y
            self.follow_start(obj, WARP_SPEED)
            self.warps_in.remove(obj)

    def event_destroy(self):
        while self in sge.game.current_room.warps:
            sge.game.current_room.warps.remove(self)


class ObjectWarpSpawn(WarpSpawn):

    def __init__(self, x, y, points=(), cls=None, interval=180, limit=None,
                 silent=False, **kwargs):
        self.cls = TYPES.get(cls)
        self.kwargs = kwargs
        self.interval = interval
        self.limit = limit
        self.silent = silent
        self.__steps_passed = interval
        self.__objects = []
        super(ObjectWarpSpawn, self).__init__(x, y, points=points)

    def event_begin_step(self, time_passed, delta_mult):
        in_view = False
        for view in sge.game.current_room.views:
            if (self.x <= view.x + view.width and self.x >= view.x and
                    self.y <= view.y + view.height and self.y >= view.y):
                in_view = True
                break

        if in_view and self.cls is not None:
            self.__steps_passed += delta_mult
            
            self.__objects = [ref for ref in self.__objects
                              if (ref() is not None and
                                  ref() in sge.game.current_room.objects)]
            if self.limit and len(self.__objects) >= self.limit:
                self.__steps_passed = 0

            while self.__steps_passed >= self.interval:
                self.__steps_passed -= self.interval
                obj = self.cls.create(self.x, self.y, **self.kwargs)
                obj.activate()
                obj.warping = True
                obj.visible = False
                obj.tangible = False
                self.follow_start(obj, WARP_SPEED)
                self.__objects.append(weakref.ref(obj))


class MovingObjectPath(xsge_path.PathLink):

    cls = None
    default_speed = ENEMY_WALK_SPEED
    default_accel = None
    default_decel = None
    default_loop = None
    auto_follow = True

    def __init__(self, x, y, path_speed=None, path_accel=None, path_decel=None,
                 path_loop=None, path_id=None, prime=False, parent=None,
                 **kwargs):
        if path_speed is None:
            path_speed = self.default_speed
        if path_accel is None:
            path_accel = self.default_accel
        if path_decel is None:
            path_decel = self.default_decel
        if path_loop is None:
            path_loop = self.default_loop

        self.path_speed = path_speed
        self.path_accel = path_accel if path_accel != -1 else None
        self.path_decel = path_decel if path_decel != -1 else None
        self.path_loop = path_loop if path_loop != -1 else None
        self.path_id = path_id
        self.prime = prime
        self.parent = parent
        self.obj = lambda: None
        super(MovingObjectPath, self).__init__(x, y, **kwargs)

    def event_create(self):
        if self.parent is not None:
            for obj in sge.game.current_room.objects:
                if (isinstance(obj, self.__class__) and
                        obj.path_id == self.parent):
                    obj.next_path = self
                    obj.next_speed = self.path_speed
                    obj.next_accel = self.path_accel
                    obj.next_decel = self.path_decel
                    obj.next_loop = self.path_loop
                    break
        else:
            self.prime = True

        if self.prime and self.cls in TYPES:
            obj = TYPES[self.cls].create(self.x, self.y, z=self.z)
            self.obj = weakref.ref(obj)
            if self.auto_follow:
                self.follow_start(obj, self.path_speed, accel=self.path_accel,
                                  decel=self.path_decel, loop=self.path_loop)


class MovingPlatformPath(MovingObjectPath):

    cls = "moving_platform"
    default_speed = 3
    default_accel = 0.02
    default_decel = 0.02

    def event_create(self):
        super(MovingPlatformPath, self).event_create()
        obj = self.obj()
        if obj:
            obj.path = self

    def follow_start(self, obj, *args, **kwargs):
        super(MovingPlatformPath, self).follow_start(obj, *args, **kwargs)
        obj.following = True

    def event_follow_end(self, obj):
        obj.following = False
        obj.speed = 0
        obj.x = self.x + self.points[-1][0]
        obj.y = self.y + self.points[-1][1]


class TriggeredMovingPlatformPath(MovingPlatformPath):

    default_speed = 2
    default_accel = None
    default_decel = None
    auto_follow = False
    followed = False


class FlyingSnowballPath(MovingObjectPath):

    cls = "flying_snowball"
    default_speed = 2
    default_accel = 0.02
    default_decel = 0.02


class FlyingSpikyPath(MovingObjectPath):

    cls = "flying_spiky"
    default_speed = 2
    default_accel = 0.02
    default_decel = 0.02


class CircoflamePath(xsge_path.Path):

    def __init__(self, x, y, z=0, points=(), rvelocity=2):
        self.rvelocity = rvelocity
        x += TILE_SIZE / 2
        y += TILE_SIZE / 2
        super(CircoflamePath, self).__init__(x, y, z=z, points=points)

    def event_create(self):
        if self.points:
            fx, fy = self.points[0]
            radius = math.hypot(fx, fy)
            pos = math.degrees(math.atan2(fy, fx))
            CircoflameCenter.create(self.x, self.y, z=self.z, radius=radius,
                                    pos=pos, rvelocity=self.rvelocity)
        self.destroy()


class MapPlayer(sge.dsp.Object):

    moving = False

    def _follow_path(self, space, path):
        if path is not None and not self.moving:
            if path.points:
                x, y = path.points[-1]
            else:
                x = 0
                y = 0
            target_space = MapSpace.get_at(path.x + x, path.y + y)
            if target_space is not None:
                if space.cleared or target_space.cleared:
                    self.moving = True
                    path.follow_start(self, MAP_SPEED)
            else:
                print("Space at position ({}, {}) doesn't exist!".format(
                    path.x + x, path.y + y))

    def move_left(self):
        space = MapSpace.get_at(self.x, self.y)
        if space is not None:
            path = space.get_left_exit()
            self._follow_path(space, path)

    def move_right(self):
        space = MapSpace.get_at(self.x, self.y)
        if space is not None:
            path = space.get_right_exit()
            self._follow_path(space, path)

    def move_up(self):
        space = MapSpace.get_at(self.x, self.y)
        if space is not None:
            path = space.get_up_exit()
            self._follow_path(space, path)

    def move_down(self):
        space = MapSpace.get_at(self.x, self.y)
        if space is not None:
            path = space.get_down_exit()
            self._follow_path(space, path)

    def move_forward(self):
        space = MapSpace.get_at(self.x, self.y)
        if space is not None:
            paths = []
            for path in space.get_exits():
                if path is not None and path.forward:
                    paths.append(path)

            if len(paths) == 1:
                self._follow_path(space, paths[0])

    def start_level(self):
        space = MapSpace.get_at(self.x, self.y)
        if space is not None:
            space.start_level()

    def event_create(self):
        global worldmap_entry_space

        start_space = MapSpace.get_at(self.x, self.y)
        if start_space is None:
            start_space = MapSpace.create(self.x, self.y)

        if worldmap_entry_space is None:
            worldmap_entry_space = start_space.ID

        if current_worldmap_space is not None:
            for obj in sge.game.current_room.objects:
                if (isinstance(obj, MapSpace) and
                        obj.ID == current_worldmap_space):
                    self.x = obj.x
                    self.y = obj.y

    def event_step(self, time_passed, delta_mult):
        global current_areas

        room = sge.game.current_room
        space = MapSpace.get_at(self.x, self.y)

        if space is not None:
            if space.level and space.level not in level_names:
                r = Level.load(space.level, True)
                if r is not None:
                    loaded_levels[space.level] = r
                    current_areas = {}
                else:
                    rush_save()
                    sge.game.start_room.start()

            room.level_text = level_names.get(space.level)
            room.level_tuxdoll_available = space.level in tuxdolls_available
            room.level_tuxdoll_found = space.level in tuxdolls_found

            key_controls = [left_key, right_key, up_key, down_key, sneak_key]
            js_controls = [left_js, right_js, up_js, down_js, sneak_js]
            states = [0 for i in key_controls]

            for i in six.moves.range(len(key_controls)):
                for player in six.moves.range(len(key_controls[i])):
                    for choice in key_controls[i][player]:
                        value = sge.keyboard.get_pressed(choice)
                        states[i] = max(states[i], value)

            for i in six.moves.range(len(js_controls)):
                for player in six.moves.range(len(key_controls[i])):
                    for choice in js_controls[i][player]:
                        j, t, c = choice
                        value = min(sge.joystick.get_value(j, t, c), 1)
                        if value >= joystick_threshold:
                            states[i] = max(states[i], value)

            left_pressed = states[0]
            right_pressed = states[1]
            up_pressed = states[2]
            down_pressed = states[3]
            sneak_pressed = states[4]

            if sneak_pressed:
                self.move_forward()
            if right_pressed - left_pressed > 0:
                self.move_right()
            elif left_pressed - right_pressed > 0:
                self.move_left()
            if down_pressed - up_pressed > 0:
                self.move_down()
            elif up_pressed - down_pressed > 0:
                self.move_up()

        if room.views:
            view = room.views[0]
            view.x = self.x - view.width / 2 + self.sprite.width / 2
            view.y = self.y - view.height / 2 + self.sprite.height / 2

    def event_key_press(self, key, char):
        if (key in itertools.chain.from_iterable(jump_key) or
                key in itertools.chain.from_iterable(action_key) or
                key in itertools.chain.from_iterable(pause_key)):
            self.start_level()
        elif key == "escape" or key in itertools.chain.from_iterable(menu_key):
            sge.game.current_room.show_menu()

    def event_joystick(self, js_name, js_id, input_type, input_id, value):
        js = (js_id, input_type, input_id)
        if value >= joystick_threshold:
            if (js in itertools.chain.from_iterable(jump_js) or
                    js in itertools.chain.from_iterable(action_js) or
                    js in itertools.chain.from_iterable(pause_js)):
                self.start_level()
            elif js in itertools.chain.from_iterable(menu_js):
                sge.game.current_room.show_menu()

    def event_stop(self):
        self.moving = False


class MapSpace(sge.dsp.Object):

    def __init__(self, x, y, level=None, level_spawn=None, ID=None, **kwargs):
        super(MapSpace, self).__init__(x, y, **kwargs)
        self.level = level
        self.level_spawn = level_spawn
        if ID is not None:
            self.ID = ID
        elif level is not None:
            self.ID = level
        else:
            self.ID = "__{}x{}__".format(x, y)

    @property
    def cleared(self):
        if self.ID == worldmap_entry_space:
            return True
        else:
            if self.level is not None:
                return self.level in cleared_levels
            else:
                connected_spaces = []
                already_checked = []
                for path in self.get_exits():
                    if path is not None:
                        x, y = path.points[-1]
                        space = MapSpace.get_at(self.x + x, self.y + y)
                        if space is not None:
                            connected_spaces.append(space)

                while connected_spaces:
                    space = connected_spaces.pop(0)
                    already_checked.append(space)
                    if (space.ID == worldmap_entry_space or
                            space.level in cleared_levels):
                        return True
                    elif space.level is None:
                        for path in space.get_exits():
                            if path is not None:
                                x, y = path.points[-1]
                                new_space = MapSpace.get_at(space.x + x,
                                                            space.y + y)
                                if (new_space is not None and
                                        new_space not in connected_spaces and
                                        new_space not in already_checked):
                                    connected_spaces.append(new_space)
                return False

    def update_sprite(self):
        if self.level is not None:
            if self.cleared:
                self.sprite = worldmap_level_complete_sprite
            else:
                self.sprite = worldmap_level_incomplete_sprite
                self.image_fps = None
        else:
            self.sprite = None

    def get_exits(self):
        """
        Return the exits of this space as a tuple in the form:
        (up, right, down, left)
        """
        exits = []
        diagonal_exits = []
        left_exit = None
        right_exit = None
        up_exit = None
        down_exit = None

        for obj in sge.game.current_room.get_objects_at(self.x - 1, self.y - 1,
                                                        2, 2):
            if (isinstance(obj, MapPath) and obj.points and
                    abs(self.x - obj.x) < 1 and abs(self.y - obj.y) < 1):
                exits.append(obj)

        # First do exits that are unambiguously one direction
        for obj in exits:
            x, y = obj.points[0]
            if x == 0:
                if y > 0:
                    if down_exit is None:
                        down_exit = obj
                elif y < 0:
                    if up_exit is None:
                        up_exit = obj
                else:
                    warnings.warn("Path at ({}, {}) has no direction!".format(
                        obj.x, obj.y))
            elif y == 0:
                if x > 0:
                    if right_exit is None:
                        right_exit = obj
                elif x < 0:
                    if left_exit is None:
                        left_exit = obj
                else:
                    warnings.warn("Path at ({}, {}) has no direction!".format(
                        obj.x, obj.y))
            else:
                diagonal_exits.append(obj)

        # And now do diagonal exits
        for obj in diagonal_exits:
            x, y = obj.points[0]
            assert x and y
            if abs(y) > abs(x):
                # Mostly vertical
                if y > 0:
                    if down_exit is None:
                        down_exit = obj
                    else:
                        if x > 0:
                            if right_exit is None:
                                right_exit = obj
                        else:
                            if left_exit is None:
                                left_exit = obj
                else:
                    if up_exit is None:
                        up_exit = obj
                    else:
                        if x > 0:
                            if right_exit is None:
                                right_exit = obj
                        else:
                            if left_exit is None:
                                left_exit = obj
            else:
                # Mostly horizontal, or equal
                if x > 0:
                    if right_exit is None:
                        right_exit = obj
                    else:
                        if y > 0:
                            if down_exit is None:
                                down_exit = obj
                        else:
                            if up_exit is None:
                                up_exit = obj
                else:
                    if left_exit is None:
                        left_exit = obj
                    else:
                        if y > 0:
                            if down_exit is None:
                                down_exit = obj
                        else:
                            if up_exit is None:
                                up_exit = obj

        return (up_exit, right_exit, down_exit, left_exit)

    def get_left_exit(self):
        return self.get_exits()[3]

    def get_right_exit(self):
        return self.get_exits()[1]

    def get_up_exit(self):
        return self.get_exits()[0]

    def get_down_exit(self):
        return self.get_exits()[2]

    def start_level(self):
        global main_area
        global level_time_bonus
        global current_areas
        global current_checkpoints

        if self.level:
            main_area = None
            current_areas = {}
            level = Level.load(self.level, True)
            if level is not None:
                checkpoint = current_checkpoints.get(self.level)
                if checkpoint is not None:
                    main_area = level.fname
                    level_time_bonus = level.time_bonus
                    area_name, area_spawn = checkpoint.split(':', 1)
                    level = Level.load(area_name, True)
                    level.spawn = area_spawn
                else:
                    level.spawn = self.level_spawn

                x = self.x - sge.game.current_room.views[0].x
                y = self.y - sge.game.current_room.views[0].y
                if self.sprite:
                    x += self.sprite.width / 2
                    y += self.sprite.height / 2
                level.start(transition="iris_in",
                            transition_time=TRANSITION_TIME,
                            transition_arg=(x, y))
            else:
                rush_save()
                sge.game.start_room.start()

    @classmethod
    def get_at(cls, x, y):
        for obj in sge.game.current_room.get_objects_at(x - 1, y - 1, 2, 2):
            if (isinstance(obj, MapSpace) and abs(x - obj.x) < 1 and
                    abs(y - obj.y) < 1):
                return obj

        return None


class MapWarp(MapSpace):

    def __init__(self, x, y, dest=None, **kwargs):
        super(MapWarp, self).__init__(x, y, **kwargs)
        self.dest = dest

    def update_sprite(self):
        self.sprite = worldmap_warp_sprite
        self.image_fps = None

    def start_level(self):
        global current_worldmap
        global current_worldmap_space
        global worldmap_entry_space
        global mapdest
        global mapdest_space

        if self.dest and ':' in self.dest:
            mapdest, mapdest_space = self.dest.split(':', 1)
        else:
            mapdest_space = None
            if self.dest:
                mapdest = self.dest

        if self.level:
            MapSpace.start_level(self)
        else:
            current_worldmap = mapdest
            current_worldmap_space = mapdest_space
            worldmap_entry_space = mapdest_space
            mapdest = None
            mapdest_space = None
            m = Worldmap.load(current_worldmap)
            m.start(transition="dissolve", transition_time=TRANSITION_TIME)
            play_sound(warp_sound)


class MapPath(xsge_path.Path):

    forward = True

    def event_create(self):
        if self.points:
            if self.forward:
                rx, ry = self.points[-1]
                rx += self.x
                ry += self.y
                rp = []
                for x, y in self.points[-2::-1] + [(0, 0)]:
                    x = x + self.x - rx
                    y = y + self.y - ry
                    rp.append((x, y))
                # Not using Object.create to prevent infinite recursion.
                m = MapPath(rx, ry, rp)
                m.forward = False
                sge.game.current_room.add(m)

            if MapSpace.get_at(self.x, self.y) is None:
                MapSpace.create(self.x, self.y)
        else:
            warnings.warn("MapPath at ({}, {}) has only one point!".format(
                self.x, self.y))

    def event_follow_end(self, obj):
        global current_worldmap_space
        global current_level

        if self.points:
            x, y = self.points[-1]
        else:
            x = 0
            y = 0

        obj.x = self.x + x
        obj.y = self.y + y
        obj.moving = False

        space = MapSpace.get_at(obj.x, obj.y)
        if space is not None and space.ID is not None:
            current_worldmap_space = space.ID

            # Save the current worldmap space as the current level.
            # This will make preloading start there next time.
            if current_worldmap_space in levels:
                current_level = levels.index(current_worldmap_space)

        save_game()


class MapWater(sge.dsp.Object):

    def __init__(self, x, y, **kwargs):
        kwargs["sprite"] = worldmap_water_sprite
        kwargs["tangible"] = False
        super(MapWater, self).__init__(x, y, **kwargs)


class Menu(xsge_gui.MenuWindow):

    items = []

    @classmethod
    def create(cls, default=0):
        if cls.items:
            self = cls.from_text(
                gui_handler, sge.game.width / 2, sge.game.height * 2 / 3,
                cls.items, font_normal=font,
                color_normal=sge.gfx.Color("white"),
                color_selected=sge.gfx.Color((0, 128, 255)),
                background_color=menu_color, margin=9, halign="center",
                valign="middle")
            default %= len(self.widgets)
            self.keyboard_focused_widget = self.widgets[default]
            self.show()
            return self

    def event_change_keyboard_focus(self):
        play_sound(select_sound)


class MainMenu(Menu):

    items = [_("New Game"), _("Load Game"), _("Select Levelset"), _("Options"),
             _("Credits"), _("Quit")]

    def event_choose(self):
        if self.choice == 0:
            play_sound(confirm_sound)
            NewGameMenu.create_page()
        elif self.choice == 1:
            play_sound(confirm_sound)
            LoadGameMenu.create_page()
        elif self.choice == 2:
            play_sound(confirm_sound)
            LevelsetMenu.create_page(refreshlist=True)
        elif self.choice == 3:
            play_sound(confirm_sound)
            OptionsMenu.create_page()
        elif self.choice == 4:
            credits_room = CreditsScreen.load(os.path.join("special",
                                                           "credits.tmx"))
            credits_room.start()
        else:
            sge.game.end()


class NewGameMenu(Menu):

    @classmethod
    def create_page(cls, default=0):
        cls.items = []
        for slot in save_slots:
            if slot is None:
                cls.items.append(_("-Empty-"))
            elif slot.get("levelset") is None:
                cls.items.append(_("-No Levelset-"))
            else:
                fname = os.path.join(DATA, "levelsets", slot["levelset"])
                try:
                    with open(fname, 'r') as f:
                        data = json.load(f)
                except (IOError, OSError, ValueError):
                    cls.items.append(_("-Corrupt Levelset-"))
                    continue
                else:
                    levelset_name = data.get("name", slot["levelset"])
                    completion = slot.get("completion", 0)
                    cls.items.append("{} ({}%)".format(levelset_name,
                                                       completion))

        cls.items.append(_("Back"))

        return cls.create(default)

    def event_choose(self):
        global abort
        global current_save_slot

        abort = False

        if self.choice in six.moves.range(len(save_slots)):
            play_sound(confirm_sound)
            current_save_slot = self.choice
            if save_slots[current_save_slot] is None:
                set_new_game()
                if not abort:
                    start_levelset()
                else:
                    NewGameMenu.create(default=self.choice)
            else:
                OverwriteConfirmMenu.create(default=1)
        else:
            play_sound(cancel_sound)
            MainMenu.create(default=0)


class OverwriteConfirmMenu(Menu):

    items = [_("Overwrite this save file"), _("Cancel")]

    def event_choose(self):
        global abort

        abort = False

        if self.choice == 0:
            play_sound(confirm_sound)
            set_new_game()
            if not abort:
                start_levelset()
            else:
                play_sound(cancel_sound)
                NewGameMenu.create(default=current_save_slot)
        else:
            play_sound(cancel_sound)
            NewGameMenu.create(default=current_save_slot)


class LoadGameMenu(NewGameMenu):

    def event_choose(self):
        global abort
        global current_save_slot

        abort = False

        if self.choice in six.moves.range(len(save_slots)):
            play_sound(confirm_sound)
            current_save_slot = self.choice
            load_game()
            if abort:
                MainMenu.create(default=1)
            elif not start_levelset():
                play_sound(error_sound)
                show_error(_("An error occurred when trying to load the game."))
                MainMenu.create(default=1)
        else:
            play_sound(cancel_sound)
            MainMenu.create(default=1)


class LevelsetMenu(Menu):

    levelsets = []
    current_levelsets = []
    page = 0

    @classmethod
    def create_page(cls, default=0, page=0, refreshlist=False):
        if refreshlist or not cls.levelsets:
            cls.levelsets = []
            for fname in os.listdir(os.path.join(DATA, "levelsets")):
                try:
                    with open(os.path.join(DATA, "levelsets", fname), 'r') as f:
                        data = json.load(f)
                except (IOError, OSError, ValueError):
                    continue
                else:
                    cls.levelsets.append((fname, str(data.get("name", "???"))))

            def sort_key(T):
                # The current levelset has top priority, followed by the
                # ReTux levelset, and every other levelset is sorted
                # alphabetically based first on their displayed names
                # and secondly on their file names.
                return (T[0] != current_levelset, T[0] != "retux.json",
                        T[1].lower(), T[0].lower())
            cls.levelsets.sort(key=sort_key)

        cls.current_levelsets = []
        cls.items = []
        if cls.levelsets:
            page_size = MENU_MAX_ITEMS - 2
            n_pages = math.ceil(len(cls.levelsets) / page_size)
            page = int(page % n_pages)
            page_start = page * page_size
            page_end = min(page_start + page_size, len(cls.levelsets))
            current_page = cls.levelsets[page_start:page_end]
            cls.current_levelsets = []
            cls.items = []
            for fname, name in current_page:
                cls.current_levelsets.append(fname)
                cls.items.append(name)

        cls.items.append(_("Next page"))
        cls.items.append(_("Back"))

        self = cls.create(default)
        self.page = page
        return self

    def event_choose(self):
        if self.choice == len(self.items) - 2:
            play_sound(select_sound)
            self.create_page(default=-2, page=self.page)
        else:
            if self.choice is not None and self.choice < len(self.items) - 2:
                play_sound(confirm_sound)
                load_levelset(self.current_levelsets[self.choice])
            else:
                play_sound(cancel_sound)

            MainMenu.create(default=2)


class OptionsMenu(Menu):

    @classmethod
    def create_page(cls, default=0):
        smt = scale_method if scale_method else "fastest"
        cls.items = [
            _("Fullscreen: {}").format(_("On") if fullscreen else _("Off")),
            _("Scale Method: {}").format(smt),
            _("Sound: {}").format(_("On") if sound_enabled else _("Off")),
            _("Music: {}").format(_("On") if music_enabled else _("Off")),
            _("Stereo: {}").format(_("On") if stereo_enabled else _("Off")),
            _("Show FPS: {}").format(_("On") if fps_enabled else _("Off")),
            _("Joystick Threshold: {}%").format(int(joystick_threshold * 100)),
            _("Configure keyboard"), _("Configure joysticks"),
            _("Detect joysticks"), _("Import levelset"), _("Export levelset"),
            _("Back")]
        return cls.create(default)

    def event_choose(self):
        global fullscreen
        global scale_method
        global sound_enabled
        global music_enabled
        global stereo_enabled
        global fps_enabled
        global joystick_threshold

        if self.choice == 0:
            play_sound(select_sound)
            fullscreen = not fullscreen
            sge.game.fullscreen = fullscreen
            OptionsMenu.create_page(default=self.choice)
        elif self.choice == 1:
            choices = [None, "noblur", "smooth"] + sge.SCALE_METHODS
            if scale_method in choices:
                i = choices.index(scale_method)
            else:
                i = 0

            play_sound(select_sound)
            i += 1
            i %= len(choices)
            scale_method = choices[i]
            sge.game.scale_method = scale_method
            OptionsMenu.create_page(default=self.choice)
        elif self.choice == 2:
            sound_enabled = not sound_enabled
            play_sound(bell_sound)
            OptionsMenu.create_page(default=self.choice)
        elif self.choice == 3:
            music_enabled = not music_enabled
            play_music(sge.game.current_room.music)
            OptionsMenu.create_page(default=self.choice)
        elif self.choice == 4:
            stereo_enabled = not stereo_enabled
            play_sound(confirm_sound)
            OptionsMenu.create_page(default=self.choice)
        elif self.choice == 5:
            play_sound(select_sound)
            fps_enabled = not fps_enabled
            OptionsMenu.create_page(default=self.choice)
        elif self.choice == 6:
            play_sound(select_sound)
            # This somewhat complicated method is to prevent rounding
            # irregularities.
            threshold = ((int(joystick_threshold * 100) + 5) % 100) / 100
            if not threshold:
                threshold = 0.0001
            joystick_threshold = threshold
            xsge_gui.joystick_threshold = threshold
            OptionsMenu.create_page(default=self.choice)
        elif self.choice == 7:
            play_sound(confirm_sound)
            KeyboardMenu.create_page()
        elif self.choice == 8:
            play_sound(confirm_sound)
            JoystickMenu.create_page()
        elif self.choice == 9:
            sge.joystick.refresh()
            play_sound(heal_sound)
            OptionsMenu.create_page(default=self.choice)
        elif self.choice == 10:
            if HAVE_TK:
                play_sound(confirm_sound)
                fname = tkinter_filedialog.askopenfilename(
                    filetypes=[(_("ReTux levelset files"), ".rtz"),
                               (_("all files"), ".*")])

                w = 400
                h = 128
                margin = 16
                x = SCREEN_SIZE[0] / 2 - w / 2
                y = SCREEN_SIZE[1] / 2 - h / 2
                c = sge.gfx.Color("black")
                window = xsge_gui.Window(gui_handler, x, y, w, h,
                                         background_color=c, border=False)

                x = margin
                y = margin
                text = _("Importing levelset...")
                c = sge.gfx.Color("white")
                xsge_gui.Label(
                    window, x, y, 1, text, font=font, width=(w - 2 * margin),
                    height=(h - 3 * margin -
                            xsge_gui.progressbar_container_sprite.height),
                    color=c)

                x = margin
                y = h - margin - xsge_gui.progressbar_container_sprite.height
                progressbar = xsge_gui.ProgressBar(window, x, y, 0,
                                                   width=(w - 2 * margin))

                window.show()
                gui_handler.event_step(0, 0)
                sge.game.refresh()

                with zipfile.ZipFile(fname, 'r') as rtz:
                    infolist = rtz.infolist()
                    for i in six.moves.range(len(infolist)):
                        member = infolist[i]
                        rtz.extract(member, DATA)
                        rtz.extract(member, os.path.join(CONFIG, "data"))
                        progressbar.progress = (i + 1) / len(infolist)
                        progressbar.redraw()
                        sge.game.pump_input()
                        gui_handler.event_step(0, 0)
                        sge.game.refresh()

                window.destroy()
                sge.game.pump_input()
                gui_handler.event_step(0, 0)
                sge.game.refresh()
                sge.game.pump_input()
                sge.game.input_events = []
            else:
                play_sound(kill_sound)
                e = _("This feature requires Tkinter, which was not successfully imported. Please make sure Tkinter is installed and try again.")
                show_error(e)
            OptionsMenu.create_page(default=self.choice)
        elif self.choice == 11:
            if HAVE_TK:
                play_sound(confirm_sound)
                ExportLevelsetMenu.create_page(refreshlist=True)
            else:
                play_sound(kill_sound)
                e = _("This feature requires Tkinter, which was not successfully imported. Please make sure Tkinter is installed and try again.")
                show_error(e)
                OptionsMenu.create_page(default=self.choice)
        else:
            play_sound(cancel_sound)
            write_to_disk()
            MainMenu.create(default=3)


class KeyboardMenu(Menu):

    page = 0

    @classmethod
    def create_page(cls, default=0, page=0):
        page %= min(len(left_key), len(right_key), len(up_key), len(down_key),
                    len(jump_key), len(action_key), len(sneak_key),
                    len(menu_key), len(pause_key))

        def format_key(key):
            if key:
                return " ".join(key)
            else:
                return None

        cls.items = [_("Player {}").format(page + 1),
                     _("Left: {}").format(format_key(left_key[page])),
                     _("Right: {}").format(format_key(right_key[page])),
                     _("Up: {}").format(format_key(up_key[page])),
                     _("Down: {}").format(format_key(down_key[page])),
                     _("Jump: {}").format(format_key(jump_key[page])),
                     _("Action: {}").format(format_key(action_key[page])),
                     _("Sneak: {}").format(format_key(sneak_key[page])),
                     _("Menu: {}").format(format_key(menu_key[page])),
                     _("Pause: {}").format(format_key(pause_key[page])),
                     _("Back")]
        self = cls.create(default)
        self.page = page
        return self

    def event_choose(self):
        def toggle_key(key, new_key, self=self):
            if new_key in key:
                if len(key) > 1:
                    key.remove(new_key)
            else:
                refused = False
                for other_key in [
                        left_key[self.page], right_key[self.page],
                        up_key[self.page], down_key[self.page],
                        jump_key[self.page], action_key[self.page],
                        sneak_key[self.page], menu_key[self.page],
                        pause_key[self.page]]:
                    if new_key in other_key:
                        if len(other_key) > 1:
                            other_key.remove(new_key)
                        else:
                            refused = True

                if not refused:
                    key.append(new_key)
                    while len(key) > 2:
                        key.pop(0)

        if self.choice == 0:
            play_sound(select_sound)
            KeyboardMenu.create_page(default=self.choice, page=(self.page + 1))
        elif self.choice == 1:
            k = wait_key()
            if k is not None:
                toggle_key(left_key[self.page], k)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 2:
            k = wait_key()
            if k is not None:
                toggle_key(right_key[self.page], k)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 3:
            k = wait_key()
            if k is not None:
                toggle_key(up_key[self.page], k)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 4:
            k = wait_key()
            if k is not None:
                toggle_key(down_key[self.page], k)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 5:
            k = wait_key()
            if k is not None:
                toggle_key(jump_key[self.page], k)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 6:
            k = wait_key()
            if k is not None:
                toggle_key(action_key[self.page], k)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 7:
            k = wait_key()
            if k is not None:
                toggle_key(sneak_key[self.page], k)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 8:
            k = wait_key()
            if k is not None:
                toggle_key(menu_key[self.page], k)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 9:
            k = wait_key()
            if k is not None:
                toggle_key(pause_key[self.page], k)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            KeyboardMenu.create_page(default=self.choice, page=self.page)
        else:
            play_sound(cancel_sound)
            OptionsMenu.create_page(default=5)


class JoystickMenu(Menu):

    page = 0

    @classmethod
    def create_page(cls, default=0, page=0):
        page %= min(len(left_js), len(right_js), len(up_js), len(down_js),
                    len(jump_js), len(action_js), len(sneak_js), len(menu_js),
                    len(pause_js))

        def format_js(js):
            js_template = "{},{},{}"
            sL = []
            for j in js:
                sL.append(js_template.format(*j))
            if sL:
                return " ".join(sL)
            else:
                return _("None")

        cls.items = [_("Player {}").format(page + 1),
                     _("Left: {}").format(format_js(left_js[page])),
                     _("Right: {}").format(format_js(right_js[page])),
                     _("Up: {}").format(format_js(up_js[page])),
                     _("Down: {}").format(format_js(down_js[page])),
                     _("Jump: {}").format(format_js(jump_js[page])),
                     _("Action: {}").format(format_js(action_js[page])),
                     _("Sneak: {}").format(format_js(sneak_js[page])),
                     _("Menu: {}").format(format_js(menu_js[page])),
                     _("Pause: {}").format(format_js(pause_js[page])),
                     _("Back")]
        self = cls.create(default)
        self.page = page
        return self

    def event_choose(self):
        def toggle_js(js, new_js, self=self):
            if new_js in js:
                js.remove(new_js)
            else:
                for other_js in [
                        left_js[self.page], right_js[self.page],
                        up_js[self.page], down_js[self.page],
                        jump_js[self.page], action_js[self.page],
                        sneak_js[self.page], menu_js[self.page],
                        pause_js[self.page]]:
                    if new_js in other_js:
                        other_key.remove(new_js)

                js.append(new_js)
                while len(js) > 2:
                    js.pop(0)

        if self.choice == 0:
            play_sound(select_sound)
            JoystickMenu.create_page(default=self.choice, page=(self.page + 1))
        elif self.choice == 1:
            js = wait_js()
            if js is not None:
                toggle_js(left_js[self.page], js)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            JoystickMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 2:
            js = wait_js()
            if js is not None:
                toggle_js(right_js[self.page], js)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            JoystickMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 3:
            js = wait_js()
            if js is not None:
                toggle_js(up_js[self.page], js)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            JoystickMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 4:
            js = wait_js()
            if js is not None:
                toggle_js(down_js[self.page], js)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            JoystickMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 5:
            js = wait_js()
            if js is not None:
                toggle_js(jump_js[self.page], js)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            JoystickMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 6:
            js = wait_js()
            if js is not None:
                toggle_js(action_js[self.page], js)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            JoystickMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 7:
            js = wait_js()
            if js is not None:
                toggle_js(sneak_js[self.page], js)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            JoystickMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 8:
            js = wait_js()
            if js is not None:
                toggle_js(menu_js[self.page], js)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            JoystickMenu.create_page(default=self.choice, page=self.page)
        elif self.choice == 9:
            js = wait_js()
            if js is not None:
                toggle_js(pause_js[self.page], js)
                set_gui_controls()
                play_sound(confirm_sound)
            else:
                play_sound(cancel_sound)
            JoystickMenu.create_page(default=self.choice, page=self.page)
        else:
            play_sound(cancel_sound)
            OptionsMenu.create_page(default=6)


class ExportLevelsetMenu(LevelsetMenu):

    def event_choose(self):
        if self.choice == len(self.items) - 2:
            play_sound(select_sound)
            self.create_page(default=-2, page=self.page)
        else:
            if self.choice is not None and self.choice < len(self.items) - 2:
                play_sound(confirm_sound)

                fname = tkinter_filedialog.asksaveasfilename(
                    defaultextension=".rtz",
                    filetypes=[(_("ReTux levelset files"), ".rtz"),
                               (_("all files"), ".*")])

                w = 400
                h = 128
                margin = 16
                x = SCREEN_SIZE[0] / 2 - w / 2
                y = SCREEN_SIZE[1] / 2 - h / 2
                c = sge.gfx.Color("black")
                window = xsge_gui.Window(gui_handler, x, y, w, h,
                                         background_color=c, border=False)

                x = margin
                y = margin
                text = _("Exporting levelset...")
                c = sge.gfx.Color("white")
                xsge_gui.Label(
                    window, x, y, 1, text, font=font, width=(w - 2 * margin),
                    height=(h - 3 * margin -
                            xsge_gui.progressbar_container_sprite.height),
                    color=c)

                x = margin
                y = h - margin - xsge_gui.progressbar_container_sprite.height
                progressbar = xsge_gui.ProgressBar(window, x, y, 0,
                                                   width=(w - 2 * margin))

                window.show()
                gui_handler.event_step(0, 0)
                sge.game.refresh()

                levelset = self.current_levelsets[self.choice]
                levelset_fname = os.path.join(DATA, "levelsets", levelset)
                with open(levelset_fname, 'r') as f:
                    data = json.load(f)
                start_cutscene = data.get("start_cutscene")
                worldmap = data.get("worldmap")
                levels = data.get("levels", [])
                include_files = data.get("include_files", [])

                def get_extra_files(fd, exclude_files):
                    if fd in exclude_files:
                        return set()

                    tmx_dir = os.path.relpath(os.path.dirname(fd), DATA)
                    extra_files = {fd}
                    exclude_files.add(fd)
                    try:
                        tilemap = tmx.TileMap.load(fd)
                    except (IOError, OSError) as e:
                        show_error(str(e))
                        return extra_files

                    for prop in tilemap.properties:
                        if prop.name == "music":
                            extra_files.add(os.path.join(DATA, "music",
                                                         prop.value))
                        elif prop.name == "timeline":
                            extra_files.add(os.path.join(DATA, "timelines",
                                                         prop.value))

                    for tileset in tilemap.tilesets:
                        ts_dir = tmx_dir
                        if tileset.source is not None:
                            extra_files.add(os.path.join(DATA, tmx_dir,
                                                         tileset.source))
                            ts_dir = os.path.dirname(os.path.join(
                                tmx_dir, tileset.source))

                        if (tileset.image is not None and
                                tileset.image.source is not None):
                            extra_files.add(os.path.join(DATA, ts_dir,
                                                         tileset.image.source))

                    def check_obj(cls, properties, exclude_files,
                                  get_extra_files=get_extra_files):
                        if cls == get_object:
                            for prop in properties:
                                if prop.name == "cls":
                                    cls = TYPES.get(prop.value,
                                                    xsge_tmx.Decoration)

                        extra_files = set()
                        for prop in properties:
                            if prop.name == "dest":
                                if ":" in prop.value:
                                    level_f, _ = prop.value.split(':', 1)
                                elif cls in {Warp, MapWarp}:
                                    level_f = prop.value
                                else:
                                    level_f = None

                                if level_f and level_f not in {
                                        "__main__", "__map__"}:
                                    if cls == MapWarp:
                                        sdir = "worldmaps"
                                    else:
                                        sdir = "levels"

                                    fname = os.path.join(DATA, sdir, level_f)
                                    extra_files |= get_extra_files(
                                        fname, exclude_files)
                            elif prop.name.endswith("timeline"):
                                extra_files.add(
                                    os.path.join(DATA, "timelines", prop.value))
                            elif prop.name == "level":
                                fname = os.path.join(DATA, "levels",
                                                     prop.value)
                                extra_files |= get_extra_files(fname,
                                                               exclude_files)

                        return extra_files

                    for layer in tilemap.layers:
                        if isinstance(layer, tmx.Layer):
                            layer_cls = TYPES.get(layer.name)
                            layer_prop = layer.properties
                            for tile in layer.tiles:
                                if tile.gid:
                                    tile_ts = None
                                    for ts in sorted(tilemap.tilesets,
                                                     key=lambda x: x.firstgid):
                                        if ts.firstgid <= tile.gid:
                                            tile_ts = ts
                                        else:
                                            break

                                    if tile_ts is not None:
                                        ts_cls = TYPES.get(tile_ts.name)
                                        ts_prop = tile_ts.properties
                                        tile_prop = []
                                        i = tile.gid - tile_ts.firstgid
                                        for tile_def in tile_ts.tiles:
                                            if tile_def.id == i:
                                                tile_prop = tile_def.properties
                                                break
                                        cls = ts_cls or layer_cls
                                        prop = layer_prop + ts_prop + tile_prop
                                        extra_files |= check_obj(cls, prop,
                                                                 exclude_files)
                        elif isinstance(layer, tmx.ObjectGroup):
                            layer_cls = TYPES.get(layer.name)
                            layer_prop = layer.properties
                            for obj in layer.objects:
                                cls = TYPES.get(obj.name) or TYPES.get(obj.type)
                                prop = obj.properties
                                if obj.gid:
                                    obj_ts = None
                                    for ts in sorted(tilemap.tilesets,
                                                     key=lambda x: x.firstgid):
                                        if ts.firstgid <= obj.gid:
                                            obj_ts = ts
                                        else:
                                            break

                                    if obj_ts is not None:
                                        ts_cls = TYPES.get(obj_ts.name)
                                        ts_prop = obj_ts.properties
                                        tile_prop = []
                                        i = obj.gid - obj_ts.firstgid
                                        for tile_def in obj_ts.tiles:
                                            if tile_def.id == i:
                                                tile_prop = tile_def.properties
                                                break
                                        cls = cls or ts_cls
                                        prop = tile_prop + prop
                                cls = cls or layer_cls
                                prop = layer_prop + prop
                                extra_files |= check_obj(cls, prop,
                                                         exclude_files)
                        elif isinstance(layer, tmx.ImageLayer):
                            extra_files |= check_obj(TYPES.get(layer.name),
                                                     layer.properties,
                                                     exclude_files)
                            if (layer.image is not None and
                                    layer.image.source is not None):
                                extra_files.add(
                                    os.path.join(DATA, tmx_dir,
                                                 layer.image.source))

                    return extra_files

                files = {levelset_fname}
                exclude_files = set()
                if start_cutscene:
                    fd = os.path.join(DATA, "levels", start_cutscene)
                    files |= get_extra_files(fd, exclude_files)
                if worldmap:
                    fd = os.path.join(DATA, "worldmaps", worldmap)
                    files |= get_extra_files(fd, exclude_files)
                for level in levels:
                    fd = os.path.join(DATA, "levels", level)
                    files |= get_extra_files(fd, exclude_files)
                for include_file in include_files:
                    files.add(os.path.join(DATA, include_file))

                files = list(files)
                inst_dir = os.path.join(os.path.dirname(__file__), "data")

                with zipfile.ZipFile(fname, 'w') as rtz:
                    for i in six.moves.range(len(files)):
                        fname = files[i]
                        aname = os.path.relpath(fname, DATA)
                        if not os.path.exists(os.path.join(inst_dir, aname)):
                            rtz.write(fname, aname)

                        progressbar.progress = (i + 1) / len(files)
                        progressbar.redraw()
                        sge.game.pump_input()
                        gui_handler.event_step(0, 0)
                        sge.game.refresh()

                window.destroy()
                sge.game.pump_input()
                gui_handler.event_step(0, 0)
                sge.game.refresh()
                sge.game.pump_input()
                sge.game.input_events = []
            else:
                play_sound(cancel_sound)

            OptionsMenu.create(default=10)


class ModalMenu(xsge_gui.MenuDialog):

    items = []

    @classmethod
    def create(cls, default=0):
        if cls.items:
            self = cls.from_text(
                gui_handler, sge.game.width / 2, sge.game.height / 2,
                cls.items, font_normal=font,
                color_normal=sge.gfx.Color("white"),
                color_selected=sge.gfx.Color((0, 128, 255)),
                background_color=menu_color, margin=9, halign="center",
                valign="middle")
            default %= len(self.widgets)
            self.keyboard_focused_widget = self.widgets[default]
            self.show()
            return self

    def event_change_keyboard_focus(self):
        play_sound(select_sound)


class PauseMenu(ModalMenu):

    @classmethod
    def create(cls, default=0):
        if LEVEL or RECORD:
            items = [_("Continue"), _("Abort")]
        elif current_worldmap:
            items = [_("Continue"), _("Return to Map"),
                     _("Return to Title Screen")]
        else:
            items = [_("Continue"), _("Return to Title Screen")]

        self = cls.from_text(
            gui_handler, sge.game.width / 2, sge.game.height / 2,
            items, font_normal=font, color_normal=sge.gfx.Color("white"),
            color_selected=sge.gfx.Color((0, 128, 255)),
            background_color=menu_color, margin=9, halign="center",
            valign="middle")
        default %= len(self.widgets)
        self.keyboard_focused_widget = self.widgets[default]
        self.show()
        return self

    def event_choose(self):
        sge.snd.Music.unpause()

        if self.choice == 1:
            rush_save()
            if current_worldmap:
                play_sound(kill_sound)

            sge.game.current_room.return_to_map()
        elif self.choice == 2:
            rush_save()
            sge.game.start_room.start()
        else:
            play_sound(select_sound)


class WorldmapMenu(ModalMenu):

    items = [_("Continue"), _("Return to Title Screen")]

    def event_choose(self):
        sge.snd.Music.unpause()

        if self.choice == 1:
            rush_save()
            sge.game.start_room.start()
        else:
            play_sound(select_sound)


class DialogLabel(xsge_gui.ProgressiveLabel):

    def event_add_character(self):
        if self.text[-1] not in (' ', '\n', '\t'):
            play_sound(type_sound)


class DialogBox(xsge_gui.Dialog):

    def __init__(self, parent, text, portrait=None, rate=TEXT_SPEED):
        width = sge.game.width / 2
        x_padding = 16
        y_padding = 16
        label_x = 8
        label_y = 8
        if portrait is not None:
            x_padding += 8
            label_x += 8
            portrait_w = portrait.width
            portrait_h = portrait.height
            label_x += portrait_w
        else:
            portrait_w = 0
            portrait_h = 0
        label_w = max(1, width - portrait_w - x_padding)
        height = max(1, portrait_h + y_padding,
                     font.get_height(text, width=label_w) + y_padding)
        x = sge.game.width / 2 - width / 2
        y = sge.game.height / 2 - height / 2
        super(DialogBox, self).__init__(
            parent, x, y, width, height,
            background_color=menu_color, border=False)
        label_h = max(1, height - y_padding)

        self.label = DialogLabel(self, label_x, label_y, 0, text, font=font,
                                 width=label_w, height=label_h,
                                 color=sge.gfx.Color("white"), rate=rate)

        if portrait is not None:
            xsge_gui.Widget(self, 8, 8, 0, sprite=portrait)

    def event_press_enter(self):
        if len(self.label.text) < len(self.label.full_text):
            self.label.text = self.label.full_text
        else:
            self.destroy()

    def event_press_escape(self):
        self.destroy()
        room = sge.game.current_room
        if (isinstance(room, Level) and
                room.timeline_skip_target is not None and
                room.timeline_step < room.timeline_skip_target):
            room.timeline_skipto(room.timeline_skip_target)


def get_object(x, y, cls=None, **kwargs):
    cls = TYPES.get(cls, xsge_tmx.Decoration)
    return cls(x, y, **kwargs)


def get_scaled_copy(obj):
    s = obj.sprite.copy()
    if obj.image_xscale < 0:
        s.mirror()
    if obj.image_yscale < 0:
        s.flip()
    s.width *= abs(obj.image_xscale)
    s.height *= abs(obj.image_yscale)
    s.rotate(obj.image_rotation)
    s.origin_x = obj.image_origin_x
    s.origin_y = obj.image_origin_y
    if obj.image_blend:
        blend_mode = obj.image_blend_mode
        if blend_mode is None:
            blend_mode = sge.BLEND_RGB_MULTIPLY
        s.draw_rectangle(0, 0, s.width, s.height, fill=obj.image_blend,
                         blend_mode=blend_mode)
    if obj.image_alpha < 255:
        c = sge.gfx.Color((255, 255, 255, obj.image_alpha))
        s.draw_rectangle(0, 0, s.width, s.height, fill=c,
                         blend_mode=sge.BLEND_RGBA_MULTIPLY)
    return s


def get_jump_speed(height, gravity=GRAVITY):
    # Get the speed to achieve a given height using a kinematic
    # equation: v[f]^2 = v[i]^2 + 2ad
    return -math.sqrt(2 * gravity * height)


def set_gui_controls():
    # Set the controls for xsge_gui based on the player controls.
    xsge_gui.next_widget_keys = (
        list(itertools.chain.from_iterable(down_key)) +
        list(itertools.chain.from_iterable(sneak_key)))
    xsge_gui.previous_widget_keys = list(itertools.chain.from_iterable(up_key))
    xsge_gui.left_keys = list(itertools.chain.from_iterable(left_key))
    xsge_gui.right_keys = list(itertools.chain.from_iterable(right_key))
    xsge_gui.up_keys = list(itertools.chain.from_iterable(up_key))
    xsge_gui.down_keys = list(itertools.chain.from_iterable(down_key))
    xsge_gui.enter_keys = (list(itertools.chain.from_iterable(jump_key)) +
                           list(itertools.chain.from_iterable(action_key)) +
                           list(itertools.chain.from_iterable(pause_key)))
    xsge_gui.escape_keys = (list(itertools.chain.from_iterable(menu_key)) +
                            ["escape"])
    xsge_gui.next_widget_joystick_events = (
        list(itertools.chain.from_iterable(down_js)) +
        list(itertools.chain.from_iterable(sneak_js)))
    xsge_gui.previous_widget_joystick_events = (
        list(itertools.chain.from_iterable(up_js)))
    xsge_gui.left_joystick_events = list(itertools.chain.from_iterable(left_js))
    xsge_gui.right_joystick_events = (
        list(itertools.chain.from_iterable(right_js)))
    xsge_gui.up_joystick_events = list(itertools.chain.from_iterable(up_js))
    xsge_gui.down_joystick_events = list(itertools.chain.from_iterable(down_js))
    xsge_gui.enter_joystick_events = (
        list(itertools.chain.from_iterable(jump_js)) +
        list(itertools.chain.from_iterable(action_js)) +
        list(itertools.chain.from_iterable(pause_js)))
    xsge_gui.escape_joystick_events = (
        list(itertools.chain.from_iterable(menu_js)))


def wait_key():
    # Wait for a key press and return it.
    sge.game.pump_input()
    sge.game.input_events = []

    while True:
        # Input events
        sge.game.pump_input()
        while sge.game.input_events:
            event = sge.game.input_events.pop(0)
            if isinstance(event, sge.input.KeyPress):
                sge.game.pump_input()
                sge.game.input_events = []
                if event.key == "escape":
                    return None
                else:
                    return event.key

        # Regulate speed
        sge.game.regulate_speed(fps=10)

        # Project text
        text = _("Press the key you wish to toggle, or Escape to cancel.")
        sge.game.project_text(font, text, sge.game.width / 2,
                              sge.game.height / 2, width=sge.game.width,
                              height=sge.game.height,
                              color=sge.gfx.Color("white"),
                              halign="center", valign="middle")

        # Refresh
        sge.game.refresh()


def wait_js():
    # Wait for a joystick press and return it.
    sge.game.pump_input()
    sge.game.input_events = []

    while True:
        # Input events
        sge.game.pump_input()
        while sge.game.input_events:
            event = sge.game.input_events.pop(0)
            if isinstance(event, sge.input.KeyPress):
                if event.key == "escape":
                    sge.game.pump_input()
                    sge.game.input_events = []
                    return None
            elif isinstance(event, sge.input.JoystickEvent):
                if (event.input_type not in {"axis0", "hat_center_x",
                                             "hat_center_y"} and
                        event.value >= joystick_threshold):
                    sge.game.pump_input()
                    sge.game.input_events = []
                    return (event.js_id, event.input_type, event.input_id)

        # Regulate speed
        sge.game.regulate_speed(fps=10)

        # Project text
        text = _("Press the joystick button, axis, or hat direction you wish to toggle, or the Escape key to cancel.")
        sge.game.project_text(font, text, sge.game.width / 2,
                              sge.game.height / 2, width=sge.game.width,
                              height=sge.game.height,
                              color=sge.gfx.Color("white"),
                              halign="center", valign="middle")

        # Refresh
        sge.game.refresh()


def show_error(message):
    if sge.game.current_room is not None:
        sge.game.pump_input()
        sge.game.input_events = []
        sge.game.mouse.visible = True
        xsge_gui.show_message(message=message, title=_("Error"),
                              buttons=[_("Ok")], width=640)
        sge.game.mouse.visible = False
    else:
        print(message)


def play_sound(sound, x=None, y=None, force=True):
    if sound_enabled and sound:
        if x is None or y is None:
            sound.play(force=force)
        else:
            current_view = None
            view_x = 0
            view_y = 0
            dist = 0
            for view in sge.game.current_room.views:
                vx = view.x + view.width / 2
                vy = view.y + view.height / 2
                new_dist = math.hypot(vx - x, vy - y)
                if current_view is None or new_dist < dist:
                    current_view = view
                    view_x = vx
                    view_y = vy
                    dist = new_dist

            bl = min(x, view_x)
            bw = abs(x - view_x)
            bt = min(y, view_y)
            bh = abs(y - view_y)
            for obj in sge.game.current_room.get_objects_at(bl, bt, bw, bh):
                if isinstance(obj, Player):
                    new_dist = math.hypot(obj.x - x, obj.y - y)
                    if new_dist < dist:
                        view_x = obj.x
                        view_y = obj.y
                        dist = new_dist

            if dist <= SOUND_MAX_RADIUS:
                volume = 1
            elif dist < SOUND_ZERO_RADIUS:
                rng = SOUND_ZERO_RADIUS - SOUND_MAX_RADIUS
                reldist = rng - (dist - SOUND_MAX_RADIUS)
                volume = min(1, abs(reldist / rng))
            else:
                # No point in continuing; it's too far away
                return

            if stereo_enabled:
                hdist = x - view_x
                if abs(hdist) < SOUND_CENTERED_RADIUS:
                    balance = 0
                else:
                    rng = SOUND_TILTED_RADIUS - SOUND_CENTERED_RADIUS
                    balance = max(-SOUND_TILT_LIMIT,
                                  min(hdist / rng, SOUND_TILT_LIMIT))
            else:
                balance = 0

            sound.play(volume=volume, balance=balance, force=force)


def play_music(music, force_restart=False):
    """Play the given music file, starting with its start piece."""
    if music_enabled and music:
        music_object = loaded_music.get(music)
        if music_object is None:
            try:
                music_object = sge.snd.Music(os.path.join(DATA, "music",
                                                          music))
            except (IOError, OSError):
                sge.snd.Music.clear_queue()
                sge.snd.Music.stop()
                return
            else:
                loaded_music[music] = music_object

        name, ext = os.path.splitext(music)
        music_start = ''.join([name, "-start", ext])
        music_start_object = loaded_music.get(music_start)
        if music_start_object is None:
            try:
                music_start_object = sge.snd.Music(os.path.join(DATA, "music",
                                                                music_start))
            except (IOError, OSError):
                pass
            else:
                loaded_music[music_start] = music_start_object

        if (force_restart or (not music_object.playing and
                              (music_start_object is None or
                               not music_start_object.playing))):
            sge.snd.Music.clear_queue()
            sge.snd.Music.stop()
            if music_start_object is not None:
                music_start_object.play()
                music_object.queue(loops=None)
            else:
                music_object.play(loops=None)
    else:
        sge.snd.Music.clear_queue()
        sge.snd.Music.stop()


def load_levelset(fname, preload_start=0):
    global current_levelset
    global start_cutscene
    global worldmap
    global loaded_worldmaps
    global levels
    global loaded_levels
    global tuxdolls_available
    global main_area

    def do_refresh():
        # Refresh the screen, return whether the user pressed a key.
        sge.game.pump_input()
        r = False
        while sge.game.input_events:
            event = sge.game.input_events.pop(0)
            if isinstance(event, sge.input.QuitRequest):
                sge.game.end()
                r = True
            elif isinstance(event, (sge.input.KeyPress,
                                    sge.input.JoystickButtonPress)):
                r = True

        gui_handler.event_step(0, 0)
        sge.game.refresh()
        return r

    if current_levelset != fname:
        current_levelset = fname

        with open(os.path.join(DATA, "levelsets", fname), 'r') as f:
            data = json.load(f)

        start_cutscene = data.get("start_cutscene")
        worldmap = data.get("worldmap")
        levels = data.get("levels", [])
        tuxdolls_available = data.get("tuxdolls_available", [])

        main_area = None

        text = _("Preloading levels...\n\n(press any key to skip)")
        label_w = font.get_width("X" * 23)
        label_h = font.get_height(text, width=label_w)
        margin = 16
        w = label_w + 2 * margin
        h = label_h + 3 * margin + xsge_gui.progressbar_container_sprite.height
        x = SCREEN_SIZE[0] / 2 - w / 2
        y = SCREEN_SIZE[1] / 2 - h / 2
        c = sge.gfx.Color("black")
        window = xsge_gui.Window(gui_handler, x, y, w, h,
                                 background_color=c, border=False)

        x = margin
        y = margin
        c = sge.gfx.Color("white")
        xsge_gui.Label(
            window, x, y, 1, text, font=font, width=label_w, height=label_h,
            color=c)

        x = margin
        y = h - margin - xsge_gui.progressbar_container_sprite.height
        progressbar = xsge_gui.ProgressBar(window, x, y, 0, width=label_w)

        window.show()
        gui_handler.event_step(0, 0)
        sge.game.refresh()

        sorted_levels = levels[preload_start:] + levels[:preload_start]
        for level in sorted_levels:
            subrooms = [level]
            already_checked = []
            done = False

            while subrooms:
                subroom = subrooms.pop(0)
                already_checked.append(subroom)
                r = Level.load(subroom)
                if r is not None:
                    loaded_levels[subroom] = r
                    for obj in r.objects:
                        if isinstance(obj, (Door, Warp)):
                            if obj.dest and ':' in obj.dest:
                                map_f = obj.dest.split(':', 1)[0]
                                if (map_f not in subrooms and
                                        map_f not in already_checked and
                                        map_f not in {"__main__", "__map__"}):
                                    subrooms.append(map_f)
                if do_refresh():
                    done = True
                    break
            else:
                progressbar.progress = ((sorted_levels.index(level) + 1) /
                                        len(sorted_levels))
                progressbar.redraw()

            if done or do_refresh():
                break

        window.destroy()
        do_refresh()
        sge.game.pump_input()
        sge.game.input_events = []


def set_new_game():
    global level_timers
    global cleared_levels
    global tuxdolls_found
    global watched_timelines
    global current_worldmap
    global current_worldmap_space
    global current_level
    global score

    if current_levelset is None:
        load_levelset(DEFAULT_LEVELSET)

    level_timers = {}
    cleared_levels = []
    tuxdolls_found = []
    watched_timelines = []
    current_worldmap = worldmap
    current_worldmap_space = None
    current_level = None
    score = 0


def write_to_disk():
    # Write our saves and settings to disk.
    keys_cfg = {"left": left_key, "right": right_key, "up": up_key,
                "down": down_key, "jump": jump_key, "action": action_key,
                "sneak": sneak_key, "menu": menu_key, "pause": pause_key}
    js_cfg = {"left": left_js, "right": right_js, "up": up_js,
              "down": down_js, "jump": jump_js, "action": action_js,
              "sneak": sneak_js, "menu": menu_js, "pause": pause_js}

    cfg = {"version": 1, "fullscreen": fullscreen,
           "scale_method": scale_method, "sound_enabled": sound_enabled,
           "music_enabled": music_enabled, "stereo_enabled": stereo_enabled,
           "fps_enabled": fps_enabled,
           "joystick_threshold": joystick_threshold, "keys": keys_cfg,
           "joystick": js_cfg}

    with open(os.path.join(CONFIG, "config.json"), 'w') as f:
        json.dump(cfg, f, indent=4)

    with open(os.path.join(CONFIG, "save_slots.json"), 'w') as f:
        json.dump(save_slots, f, indent=4)


def save_game():
    global save_slots

    if current_save_slot is not None:
        if levels:
            completion = int(100 * (len(cleared_levels) + len(tuxdolls_found)) /
                             (len(levels) + len(tuxdolls_available)))
            if completion == 0 and (cleared_levels or tuxdolls_found):
                completion = 1
            elif (completion == 100 and
                  (len(cleared_levels) < len(levels) or
                   len(tuxdolls_found) < len(tuxdolls_available))):
                completion = 99
        else:
            completion = 100

        save_slots[current_save_slot] = {
            "levelset": current_levelset, "level_timers": level_timers,
            "cleared_levels": cleared_levels, "tuxdolls_found": tuxdolls_found,
            "watched_timelines": watched_timelines,
            "current_worldmap": current_worldmap,
            "current_worldmap_space": current_worldmap_space,
            "worldmap_entry_space": worldmap_entry_space,
            "current_level": current_level,
            "current_checkpoints": current_checkpoints, "score": score,
            "completion": completion}

    write_to_disk()


def load_game():
    global level_timers
    global cleared_levels
    global tuxdolls_found
    global watched_timelines
    global current_worldmap
    global current_worldmap_space
    global worldmap_entry_space
    global current_level
    global current_checkpoints
    global score

    if (current_save_slot is not None and
            save_slots[current_save_slot] is not None and
            save_slots[current_save_slot].get("levelset") is not None):
        slot = save_slots[current_save_slot]
        level_timers = slot.get("level_timers", {})
        cleared_levels = slot.get("cleared_levels", [])
        tuxdolls_found = slot.get("tuxdolls_found", [])
        watched_timelines = slot.get("watched_timelines", [])
        current_worldmap = slot.get("current_worldmap")
        current_worldmap_space = slot.get("current_worldmap_space")
        worldmap_entry_space = slot.get("worldmap_entry_space")
        current_level = slot.get("current_level", 0)
        current_checkpoints = slot.get("current_checkpoints", {})
        score = slot.get("score", 0)
        load_levelset(slot["levelset"], current_level)
    else:
        set_new_game()


def rush_save():
    global level_timers
    global cleared_levels
    global score
    global main_area

    if main_area is not None:
        if not cleared_levels and current_checkpoints.get(main_area) is None:
            level_timers[main_area] = level_time_bonus

        won = (isinstance(sge.game.current_room, Level) and
               sge.game.current_room.won)

        if won:
            score += sge.game.current_room.points
            sge.game.current_room.points = 0
            if main_area not in cleared_levels:
                cleared_levels.append(main_area)

        if won or level_timers.setdefault(main_area, 0) < 0:
            score += level_timers[main_area]
            level_timers[main_area] = 0

    save_game()
    main_area = None


def start_levelset():
    global current_level
    global main_area
    global level_cleared
    global current_areas
    current_areas = {}
    main_area = None
    level_cleared = True

    if start_cutscene and current_level is None:
        current_level = 0
        level = Level.load(start_cutscene, True)
        if level is not None:
            level.start()
        else:
            return False
    elif current_worldmap:
        m = Worldmap.load(current_worldmap)
        m.start()
    else:
        if current_level is None:
            current_level = 0

        if current_level < len(levels):
            level = Level.load(levels[current_level], True)
            if level is not None:
                level.start()
            else:
                return False
        else:
            print("Invalid save file: current level does not exist.")
            return False

    return True


def warp(dest):
    if dest == "__map__":
        sge.game.current_room.return_to_map(True)
    else:
        cr = sge.game.current_room

        if ":" in dest:
            level_f, spawn = dest.split(':', 1)
        else:
            level_f = None
            spawn = dest

        if level_f == "__main__":
            level_f = main_area

        if level_f:
            level = sge.game.current_room.__class__.load(level_f, True)
        else:
            level = cr

        if level is not None:
            level.spawn = spawn
            level.points = cr.points

            for nobj in level.objects[:]:
                if isinstance(nobj, Player):
                    for cobj in cr.objects[:]:
                        if (isinstance(cobj, Player) and
                                cobj.player == nobj.player):
                            nobj.hp = cobj.hp
                            nobj.coins = cobj.coins
                            nobj.facing = cobj.facing
                            nobj.image_xscale = cobj.image_xscale
                            nobj.image_yscale = cobj.image_yscale

                            held_object = cobj.held_object
                            if held_object is not None:
                                cobj.drop_object()
                                cr.remove(held_object)
                                level.add(held_object)
                                nobj.pickup(held_object)

                            break

            level.start()
        else:
            # Error occurred; restart the game.
            rush_save()
            sge.game.start_room.start()


TYPES = {"solid_left": SolidLeft, "solid_right": SolidRight,
         "solid_top": SolidTop, "solid_bottom": SolidBottom, "solid": Solid,
         "slope_topleft": SlopeTopLeft, "slope_topright": SlopeTopRight,
         "slope_bottomleft": SlopeBottomLeft,
         "slope_bottomright": SlopeBottomRight,
         "moving_platform": MovingPlatform, "spike_left": SpikeLeft,
         "spike_right": SpikeRight, "spike_top": SpikeTop,
         "spike_bottom": SpikeBottom, "death": Death, "level_end": LevelEnd,
         "creatures": get_object, "hazards": get_object,
         "special_blocks": get_object, "decoration_small": get_object,
         "map_objects": get_object, "player": Player,
         "walking_snowball": WalkingSnowball,
         "bouncing_snowball": BouncingSnowball,
         "walking_iceblock": WalkingIceblock, "spiky": Spiky,
         "bomb": WalkingBomb, "jumpy": Jumpy,
         "flying_snowball": FlyingSnowball, "flying_spiky": FlyingSpiky,
         "icicle": Icicle, "steady_icicle": SteadyIcicle,
         "raccot_icicle": RaccotIcicle, "krush": Krush, "krosh": Krosh,
         "circoflame": CircoflamePath, "circoflamecenter": CircoflameCenter,
         "snowman": Snowman, "raccot": Raccot, "fireflower": FireFlower,
         "iceflower": IceFlower, "tuxdoll": TuxDoll, "rock": Rock,
         "fixed_spring": FixedSpring, "spring": Spring,
         "rusty_spring": RustySpring, "lantern": Lantern,
         "timeline_switcher": TimelineSwitcher, "iceblock": Iceblock,
         "boss_block": BossBlock, "brick": Brick, "coinbrick": CoinBrick,
         "emptyblock": EmptyBlock, "itemblock": ItemBlock,
         "hiddenblock": HiddenItemBlock, "infoblock": InfoBlock,
         "thin_ice": ThinIce, "lava": Lava, "lava_surface": LavaSurface,
         "goal": Goal, "goal_top": GoalTop, "coin": Coin, "warp": Warp,
         "moving_platform_path": MovingPlatformPath,
         "triggered_moving_platform_path": TriggeredMovingPlatformPath,
         "flying_snowball_path": FlyingSnowballPath,
         "flying_spiky_path": FlyingSpikyPath, "spawn": Spawn,
         "checkpoint": Checkpoint, "bell": Bell, "door": Door,
         "warp_spawn": WarpSpawn, "object_warp_spawn": ObjectWarpSpawn,
         "map_player": MapPlayer, "map_level": MapSpace, "map_warp": MapWarp,
         "map_path": MapPath, "map_water": MapWater}


print(_("Initializing game system..."))
Game(SCREEN_SIZE[0], SCREEN_SIZE[1], fps=FPS, delta=DELTA, delta_min=DELTA_MIN,
     delta_max=DELTA_MAX, window_text="reTux {}".format(__version__),
     window_icon=os.path.join(DATA, "images", "misc", "icon.png"))

print(_("Initializing GUI system..."))
xsge_gui.init()
gui_handler = xsge_gui.Handler()

menu_color = sge.gfx.Color((128, 128, 255, 192))

# Load sprites
print(_("Loading images..."))
d = os.path.join(DATA, "images", "objects", "tux")
tux_body_stand_sprite = sge.gfx.Sprite(
    "tux_body_stand", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_stand_sprite = sge.gfx.Sprite(
    "tux_arms_stand", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_walk_sprite = sge.gfx.Sprite(
    "tux_body_walk", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_walk_sprite = sge.gfx.Sprite(
    "tux_arms_walk", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_run_sprite = sge.gfx.Sprite(
    "tux_body_run", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_run_sprite = sge.gfx.Sprite(
    "tux_arms_run", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_skid_sprite = sge.gfx.Sprite(
    "tux_body_skid", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_skid_sprite = sge.gfx.Sprite(
    "tux_arms_skid", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_jump_sprite = sge.gfx.Sprite(
    "tux_body_jump", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_jump_sprite = sge.gfx.Sprite(
    "tux_arms_jump", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_fall_sprite = tux_body_jump_sprite.copy()
tux_arms_fall_sprite = sge.gfx.Sprite(
    "tux_arms_fall", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_kick_sprite = sge.gfx.Sprite(
    "tux_body_kick", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_kick_sprite = sge.gfx.Sprite(
    "tux_arms_kick", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_grab_sprite = sge.gfx.Sprite(
    "tux_arms_grab", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_skid_grab_sprite = sge.gfx.Sprite(
    "tux_arms_skid_grab", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_die_sprite = sge.gfx.Sprite("tux_die", d, origin_x=29, origin_y=11, fps=8)
tux_offscreen_sprite = sge.gfx.Sprite("tux_offscreen", d, origin_x=16)

tux_stand_sprite = tux_body_stand_sprite.copy()
tux_walk_sprite = tux_body_walk_sprite.copy()
tux_run_sprite = tux_body_run_sprite.copy()
tux_skid_sprite = tux_body_skid_sprite.copy()
tux_jump_sprite = tux_body_jump_sprite.copy()
tux_fall_sprite = tux_body_fall_sprite.copy()
tux_kick_sprite = tux_body_kick_sprite.copy()

for bs, a in [(tux_stand_sprite, tux_arms_stand_sprite),
              (tux_walk_sprite, tux_arms_walk_sprite),
              (tux_run_sprite, tux_arms_run_sprite),
              (tux_skid_sprite, tux_arms_skid_sprite),
              (tux_jump_sprite, tux_arms_jump_sprite),
              (tux_fall_sprite, tux_arms_fall_sprite),
              (tux_kick_sprite, tux_arms_kick_sprite)]:
    for i in six.moves.range(bs.frames):
        bs.draw_sprite(a, i, bs.origin_x, bs.origin_y, i)

d = os.path.join(DATA, "images", "objects", "enemies")
snowball_walk_sprite = sge.gfx.Sprite("snowball", d, origin_x=19, origin_y=4,
                                      fps=8, bbox_x=-13, bbox_y=0,
                                      bbox_width=26, bbox_height=32)
bouncing_snowball_sprite = sge.gfx.Sprite(
    "bouncing_snowball", d, origin_x=17, origin_y=0, fps=8, bbox_x=-13,
    bbox_y=0, bbox_width=26, bbox_height=32)
snowball_squished_sprite = sge.gfx.Sprite("snowball_squished", d, origin_x=17,
                                          origin_y=-19, bbox_x=-13, bbox_y=19,
                                          bbox_width=26, bbox_height=13)
iceblock_walk_sprite = sge.gfx.Sprite(
    "iceblock", d, origin_x=18, origin_y=6, fps=10, bbox_x=-13, bbox_y=1,
    bbox_width=25, bbox_height=31)
iceblock_flat_sprite = sge.gfx.Sprite("iceblock_flat", d, origin_x=18,
                                      origin_y=3, bbox_x=-16, bbox_y=4,
                                      bbox_width=31, bbox_height=28)
spiky_walk_sprite = sge.gfx.Sprite("spiky", d, origin_x=22, origin_y=10, fps=8,
                                   bbox_x=-13, bbox_y=0, bbox_width=26,
                                   bbox_height=32)
spiky_iced_sprite = sge.gfx.Sprite("spiky_iced", d, origin_x=22, origin_y=10,
                                   fps=THAW_FPS, bbox_x=-13, bbox_y=0,
                                   bbox_width=26, bbox_height=32)
spiky_iced_sprite.append_frame()
spiky_iced_sprite.draw_sprite(spiky_walk_sprite, 1, spiky_walk_sprite.origin_x,
                              spiky_walk_sprite.origin_y, frame=1)
bomb_walk_sprite = sge.gfx.Sprite("bomb", d, origin_x=21, origin_y=8, fps=8,
                                  bbox_x=-13, bbox_y=0, bbox_width=26,
                                  bbox_height=32)
bomb_iced_sprite = sge.gfx.Sprite("bomb_iced", d, origin_x=21, origin_y=8,
                                  fps=THAW_FPS, bbox_x=-13, bbox_y=0,
                                  bbox_width=26, bbox_height=32)
bomb_iced_sprite.append_frame()
bomb_iced_sprite.draw_sprite(bomb_walk_sprite, 1, bomb_iced_sprite.origin_x,
                             bomb_iced_sprite.origin_y, frame=1)
bomb_ticking_sprite = sge.gfx.Sprite(
    "bomb_ticking", d, origin_x=21, origin_y=5, bbox_x=-13, bbox_y=3,
    bbox_width=26, bbox_height=29)
bomb_ticking_sprite.fps = bomb_ticking_sprite.frames / BOMB_TICK_TIME
jumpy_sprite = sge.gfx.Sprite("jumpy", d, origin_x=24, origin_y=13, bbox_x=-16,
                              bbox_y=0, bbox_width=32, bbox_height=32)
jumpy_bounce_sprite = sge.gfx.Sprite(
    "jumpy_bounce", d, origin_x=24, origin_y=13, bbox_x=-16, bbox_y=0,
    bbox_width=32, bbox_height=32)
jumpy_iced_sprite = sge.gfx.Sprite("jumpy_iced", d, origin_x=24, origin_y=13,
                                   fps=THAW_FPS, bbox_x=-16, bbox_y=0,
                                   bbox_width=32, bbox_height=32)
jumpy_iced_sprite.append_frame()
jumpy_iced_sprite.draw_sprite(jumpy_sprite, 0, jumpy_sprite.origin_x,
                              jumpy_sprite.origin_y, frame=1)
flying_snowball_sprite = sge.gfx.Sprite(
    "flying_snowball", d, origin_x=20, origin_y=11, fps=15, bbox_x=-13,
    bbox_y=0, bbox_width=26, bbox_height=32)
flying_snowball_squished_sprite = sge.gfx.Sprite(
    "flying_snowball_squished", d, origin_x=20, origin_y=-11, bbox_x=-13,
    bbox_y=11, bbox_width=26, bbox_height=21)
flying_spiky_sprite = sge.gfx.Sprite("flying_spiky", d, origin_x=24,
                                     origin_y=14, fps=15, bbox_x=-13, bbox_y=0,
                                     bbox_width=26, bbox_height=32)
flying_spiky_iced_sprite = sge.gfx.Sprite(
    "flying_spiky_iced", d, origin_x=24, origin_y=14, fps=THAW_FPS, bbox_x=-13,
    bbox_y=0, bbox_width=26, bbox_height=32)
flying_spiky_iced_sprite.append_frame()
flying_spiky_iced_sprite.draw_sprite(flying_spiky_sprite, 0,
                                     flying_spiky_sprite.origin_x,
                                     flying_spiky_sprite.origin_y, frame=1)
icicle_sprite = sge.gfx.Sprite("icicle", d, bbox_x=0, bbox_y=0, bbox_width=32,
                               bbox_height=48)
icicle_broken_sprite = sge.gfx.Sprite("icicle_broken", d, bbox_x=0, bbox_y=32,
                                      bbox_width=32, bbox_height=16)
krush_sprite = sge.gfx.Sprite("krush", d, origin_x=1, bbox_x=0, bbox_y=0,
                              bbox_width=64, bbox_height=64)
krosh_sprite = sge.gfx.Sprite("krosh", d, origin_x=2, bbox_x=0, bbox_y=0,
                              bbox_width=128, bbox_height=128)
circoflame_sprite = sge.gfx.Sprite("circoflame", d, origin_x=16, origin_y=16,
                                   fps=8, bbox_x=-8, bbox_y=-8, bbox_width=16,
                                   bbox_height=16)
snowman_stand_sprite = sge.gfx.Sprite("snowman_stand", d, origin_x=28,
                                      origin_y=43, bbox_x=-17, bbox_y=-40,
                                      bbox_width=34, bbox_height=72)
snowman_walk_sprite = sge.gfx.Sprite("snowman_walk", d, origin_x=28,
                                     origin_y=43, bbox_x=-17, bbox_y=-40,
                                     bbox_width=34, bbox_height=72)
snowman_jump_sprite = sge.gfx.Sprite("snowman_jump", d, origin_x=28,
                                     origin_y=43, bbox_x=-17, bbox_y=-40,
                                     bbox_width=34, bbox_height=72)
snowman_hurt_walk_sprite = sge.gfx.Sprite("snowman_hurt_walk", d, origin_x=28,
                                          origin_y=43, bbox_x=-17, bbox_y=-8,
                                          bbox_width=34, bbox_height=40)
snowman_hurt_jump_sprite = sge.gfx.Sprite("snowman_hurt_jump", d, origin_x=28,
                                          origin_y=43, bbox_x=-17, bbox_y=-8,
                                          bbox_width=34, bbox_height=40)
raccot_stand_sprite = sge.gfx.Sprite("raccot_stand", d, origin_x=41,
                                     origin_y=74, bbox_x=-30, bbox_y=-64,
                                     bbox_width=60, bbox_height=96)
raccot_walk_sprite = sge.gfx.Sprite("raccot_walk", d, origin_x=54, origin_y=76,
                                    bbox_x=-30, bbox_y=-64, bbox_width=60,
                                    bbox_height=96)
raccot_stomp_sprite = sge.gfx.Sprite("raccot_stomp", d, origin_x=41,
                                     origin_y=77, bbox_x=-30, bbox_y=-64,
                                     bbox_width=60, bbox_height=96)
raccot_hop_sprite = sge.gfx.Sprite("raccot_hop", d, origin_x=41, origin_y=74,
                                   bbox_x=-30, bbox_y=-64, bbox_width=60,
                                   bbox_height=96)
raccot_jump_sprite = sge.gfx.Sprite("raccot_jump", d, origin_x=60, origin_y=72,
                                    bbox_x=-30, bbox_y=-64, bbox_width=60,
                                    bbox_height=96)

d = os.path.join(DATA, "images", "objects", "bonus")
bonus_empty_sprite = sge.gfx.Sprite("bonus_empty", d)
bonus_full_sprite = sge.gfx.Sprite("bonus_full", d, fps=8)
brick_sprite = sge.gfx.Sprite("brick", d)
brick_shard_sprite = sge.gfx.Sprite("brick_shard", d)
coin_sprite = sge.gfx.Sprite("coin", d, fps=8)
fire_flower_sprite = sge.gfx.Sprite("fire_flower", d, origin_x=16, origin_y=16,
                                    fps=8, bbox_x=-8, bbox_y=-8, bbox_width=16,
                                    bbox_height=24)
ice_flower_sprite = sge.gfx.Sprite("ice_flower", d, origin_x=16, origin_y=16,
                                   fps=8, bbox_x=-8, bbox_y=-8, bbox_width=16,
                                   bbox_height=24)
tuxdoll_sprite = sge.gfx.Sprite("tuxdoll", d, origin_x=16, origin_y=16,
                                bbox_x=-16, bbox_y=-16, bbox_width=32,
                                bbox_height=32)

tuxdoll_transparent_sprite = tuxdoll_sprite.copy()
eraser = sge.gfx.Sprite(width=tuxdoll_transparent_sprite.width,
                        height=tuxdoll_transparent_sprite.height)
eraser.draw_rectangle(0, 0, eraser.width, eraser.height,
                      fill=sge.gfx.Color((0, 0, 0, 128)))
tuxdoll_transparent_sprite.draw_sprite(eraser, 0, 0, 0,
                                       blend_mode=sge.BLEND_RGBA_SUBTRACT)
del eraser

tuxdoll_shadow_sprite = tuxdoll_sprite.copy()
darkener = sge.gfx.Sprite(width=tuxdoll_shadow_sprite.width,
                          height=tuxdoll_shadow_sprite.height)
darkener.draw_rectangle(0, 0, darkener.width, darkener.height,
                        fill=sge.gfx.Color("black"))
tuxdoll_shadow_sprite.draw_sprite(darkener, 0, 0, 0,
                                  blend_mode=sge.BLEND_RGB_MINIMUM)
del darkener

d = os.path.join(DATA, "images", "objects", "decoration")
lava_body_sprite = sge.gfx.Sprite("lava_body", d, transparent=False, fps=5)
lava_surface_sprite = sge.gfx.Sprite("lava_surface", d, fps=5)
goal_sprite = sge.gfx.Sprite("goal", d, fps=8)
goal_top_sprite = sge.gfx.Sprite("goal_top", d, fps=8)

d = os.path.join(DATA, "images", "objects", "spring")
fixed_spring_sprite = sge.gfx.Sprite(
    "fixed_spring", d, origin_x=16, origin_y=16, bbox_x=-16, bbox_y=-7,
    bbox_width=32, bbox_height=23)
fixed_spring_expand_sprite = sge.gfx.Sprite(
    "fixed_spring_expand", d, origin_x=16, origin_y=16, fps=16, bbox_x=-16,
    bbox_y=-7, bbox_width=32, bbox_height=23)
spring_sprite = sge.gfx.Sprite("spring", d, origin_x=16, origin_y=16,
                               bbox_x=-16, bbox_y=-7, bbox_width=32,
                               bbox_height=23)
spring_expand_sprite = sge.gfx.Sprite(
    "spring_expand", d, origin_x=16, origin_y=16, fps=16, bbox_x=-16,
    bbox_y=-7, bbox_width=32, bbox_height=23)
rusty_spring_sprite = sge.gfx.Sprite(
    "rusty_spring", d, origin_x=16, origin_y=16, bbox_x=-16, bbox_y=-7,
    bbox_width=32, bbox_height=23)
rusty_spring_expand_sprite = sge.gfx.Sprite(
    "rusty_spring_expand", d, origin_x=16, origin_y=26, fps=16, bbox_x=-16,
    bbox_y=-7, bbox_width=32, bbox_height=23)
rusty_spring_dead_sprite = sge.gfx.Sprite(
    "rusty_spring_dead", d, origin_x=16, origin_y=26, bbox_x=-16, bbox_y=-7,
    bbox_width=32, bbox_height=23)

d = os.path.join(DATA, "images", "objects", "misc")
platform_sprite = sge.gfx.Sprite("platform", d)
rock_sprite = sge.gfx.Sprite("rock", d)
lantern_sprite = sge.gfx.Sprite("lantern", d, origin_x=20, origin_y=9, fps=10,
                                bbox_x=-16, bbox_y=0, bbox_width=32,
                                bbox_height=32)
iceblock_sprite = sge.gfx.Sprite("iceblock", d)
iceblock_melt_sprite = sge.gfx.Sprite("iceblock_melt", d, fps=30)
thin_ice_sprite = sge.gfx.Sprite("thin_ice", d, fps=0)
thin_ice_break_sprite = sge.gfx.Sprite("thin_ice_break", d, fps=8)
boss_block_sprite = sge.gfx.Sprite("boss_block", d, transparent=False,
                                   origin_x=16, origin_y=16)
bell_sprite = sge.gfx.Sprite("bell", d, origin_x=-1, fps=10, bbox_x=0,
                             bbox_width=32, bbox_height=32)
door_sprite = sge.gfx.Sprite("door", d, origin_x=25, origin_y=68, fps=10)
door_back_sprite = sge.gfx.Sprite("door_back", d, origin_x=21, origin_y=41,
                                  transparent=False)

d = os.path.join(DATA, "images", "portraits")
portrait_sprites = {}
for fname in os.listdir(d):
    root, ext = os.path.splitext(fname)
    try:
        portrait = sge.gfx.Sprite(root, d)
    except (IOError, OSError):
        pass
    else:
        portrait_sprites[root] = portrait

d = os.path.join(DATA, "images", "misc")
logo_sprite = sge.gfx.Sprite("logo", d, origin_x=140)
fire_bullet_sprite = sge.gfx.Sprite("fire_bullet", d, origin_x=8, origin_y=8,
                                    fps=8, bbox_x=-8, bbox_width=16)
ice_bullet_sprite = sge.gfx.Sprite("ice_bullet", d, origin_x=8, origin_y=7,
                                   bbox_width=32)
ice_bullet_break_sprite = sge.gfx.Sprite("ice_bullet_break", d, origin_x=8,
                                         origin_y=7, fps=24)
explosion_sprite = sge.gfx.Sprite("explosion", d, origin_x=32, origin_y=19,
                                  fps=15, bbox_x=-28, bbox_y=-11,
                                  bbox_width=56, bbox_height=48)
smoke_puff_sprite = sge.gfx.Sprite("smoke_puff", d, width=48, height=48,
                                   origin_x=24, origin_y=24, fps=24)
smoke_plume_sprite = sge.gfx.Sprite("smoke_plume", d, width=64, height=64,
                                    origin_x=32, origin_y=32, fps=30)
fireball_smoke_sprite = sge.gfx.Sprite("smoke_plume", d, width=16, height=16,
                                       origin_x=8, origin_y=8, fps=30)
item_spawn_cloud_sprite = sge.gfx.Sprite("smoke_plume", d, width=80, height=80,
                                         origin_x=40, origin_y=40, fps=30)
item_spawn_cloud_sprite.delete_frame(0)
light_sprite = sge.gfx.Sprite("light", d, origin_x=192, origin_y=192)
light_small_sprite = sge.gfx.Sprite("light_small", d, origin_x=64, origin_y=64)
light_tiny_sprite = sge.gfx.Sprite("light_tiny", d, origin_x=32, origin_y=32)
heart_empty_sprite = sge.gfx.Sprite("heart_empty", d, origin_y=-1)
heart_full_sprite = sge.gfx.Sprite("heart_full", d, origin_y=-1)

fire_flower_light_sprite = light_small_sprite.copy()
blender = sge.gfx.Sprite(width=fire_flower_light_sprite.width,
                         height=fire_flower_light_sprite.height)
blender.draw_rectangle(0, 0, blender.width, blender.height,
                       fill=sge.gfx.Color("#F1670B"))
fire_flower_light_sprite.draw_sprite(blender, 0, 0, 0,
                                     blend_mode=sge.BLEND_RGB_MULTIPLY)
del blender

ice_flower_light_sprite = light_small_sprite.copy()
blender = sge.gfx.Sprite(width=ice_flower_light_sprite.width,
                         height=ice_flower_light_sprite.height)
blender.draw_rectangle(0, 0, blender.width, blender.height,
                       fill=sge.gfx.Color("#7CF8FA"))
ice_flower_light_sprite.draw_sprite(blender, 0, 0, 0,
                                    blend_mode=sge.BLEND_RGB_MULTIPLY)
del blender

fireball_light_sprite = light_tiny_sprite.copy()
blender = sge.gfx.Sprite(width=fireball_light_sprite.width,
                         height=fireball_light_sprite.height)
blender.draw_rectangle(0, 0, blender.width, blender.height,
                       fill=sge.gfx.Color("#FF5B11"))
fireball_light_sprite.draw_sprite(blender, 0, 0, 0,
                                  blend_mode=sge.BLEND_RGB_MULTIPLY)
del blender

explosion_light_sprite = light_small_sprite.copy()
blender = sge.gfx.Sprite(width=fire_flower_light_sprite.width,
                         height=fire_flower_light_sprite.height)
blender.draw_rectangle(0, 0, blender.width, blender.height,
                       fill=sge.gfx.Color("#FFBC00"))
explosion_light_sprite.draw_sprite(blender, 0, 0, 0,
                                   blend_mode=sge.BLEND_RGB_MULTIPLY)
del blender

circoflame_light_sprite = light_tiny_sprite.copy()
blender = sge.gfx.Sprite(width=fireball_light_sprite.width,
                         height=fireball_light_sprite.height)
blender.draw_rectangle(0, 0, blender.width, blender.height,
                       fill=sge.gfx.Color("#D5CD49"))
circoflame_light_sprite.draw_sprite(blender, 0, 0, 0,
                                    blend_mode=sge.BLEND_RGB_MULTIPLY)
del blender

coin_icon_sprite = coin_sprite.copy()
coin_icon_sprite.width = 16
coin_icon_sprite.height = 16
coin_icon_sprite.origin_y = -1

d = os.path.join(DATA, "images", "worldmap")
worldmap_tux_sprite = sge.gfx.Sprite("tux", d)
worldmap_level_complete_sprite = sge.gfx.Sprite("level_complete", d)
worldmap_level_incomplete_sprite = sge.gfx.Sprite("level_incomplete", d, fps=8)
worldmap_warp_sprite = sge.gfx.Sprite("warp", d, fps=3)
worldmap_water_sprite = sge.gfx.Sprite("water", d, transparent=False, fps=8)

# Load backgrounds
d = os.path.join(DATA, "images", "backgrounds")
layers = []

if not NO_BACKGROUNDS:
    layers = [
        sge.gfx.BackgroundLayer(
            sge.gfx.Sprite("arctis1-middle", d), 0, 0, -100000,
            xscroll_rate=0.5, yscroll_rate=0.5, repeat_left=True,
            repeat_right=True),
        sge.gfx.BackgroundLayer(
            sge.gfx.Sprite("arctis1-bottom", d, transparent=False), 0, 352,
            -100000, xscroll_rate=0.5, yscroll_rate=0.5, repeat_left=True,
            repeat_right=True, repeat_down=True),
        sge.gfx.BackgroundLayer(
            sge.gfx.Sprite("arctis2-middle", d), 0, 0, -100010,
            xscroll_rate=0.25, yscroll_rate=0.25, repeat_left=True,
            repeat_right=True),
        sge.gfx.BackgroundLayer(
            sge.gfx.Sprite("arctis2-bottom", d, transparent=False), 0, 352,
            -100010, xscroll_rate=0.25, yscroll_rate=0.25, repeat_left=True,
            repeat_right=True, repeat_down=True),
        sge.gfx.BackgroundLayer(
            sge.gfx.Sprite("arctis3", d, transparent=False), 0, 0, -100020,
            xscroll_rate=0, yscroll_rate=0.25, repeat_left=True,
            repeat_right=True)]

backgrounds["arctis"] = sge.gfx.Background(layers,
                                           sge.gfx.Color((109, 92, 230)))

if not NO_BACKGROUNDS:
    cave_edge_spr = sge.gfx.Sprite("cave-edge", d, transparent=False)
    layers = [
        sge.gfx.BackgroundLayer(
            sge.gfx.Sprite("cave-middle", d, transparent=False), 0, 128,
            -100000, xscroll_rate=0.7, yscroll_rate=0.7, repeat_left=True,
            repeat_right=True),
        sge.gfx.BackgroundLayer(
            cave_edge_spr, 0, 0, -100000, xscroll_rate=0.7, yscroll_rate=0.7,
            repeat_left=True, repeat_right=True, repeat_up=True),
        sge.gfx.BackgroundLayer(
            cave_edge_spr, 0, 256, -100000, xscroll_rate=0.7, yscroll_rate=0.7,
            repeat_left=True, repeat_right=True, repeat_down=True)]
    del cave_edge_spr

backgrounds["cave"] = sge.gfx.Background(layers, sge.gfx.Color("#024"))

if not NO_BACKGROUNDS:
    nightsky_bottom_spr = sge.gfx.Sprite("nightsky-bottom", d,
                                         transparent=False)
    layers = [
        sge.gfx.BackgroundLayer(
            sge.gfx.Sprite("nightsky1-middle", d), 0, 306, -100000,
            xscroll_rate=0.5, yscroll_rate=0.5, repeat_left=True,
            repeat_right=True),
        sge.gfx.BackgroundLayer(
            nightsky_bottom_spr, 0, 664, -100000, xscroll_rate=0.5,
            yscroll_rate=0.5, repeat_left=True, repeat_right=True,
            repeat_down=True),
        sge.gfx.BackgroundLayer(
            sge.gfx.Sprite("nightsky2-middle", d, transparent=False), 0, 0,
            -100010, xscroll_rate=0.25, yscroll_rate=0.25, repeat_left=True,
            repeat_right=True),
        sge.gfx.BackgroundLayer(
            sge.gfx.Sprite("nightsky2-top", d, transparent=False), 0, -600,
            -100010, xscroll_rate=0.25, yscroll_rate=0.25, repeat_left=True,
            repeat_right=True, repeat_up=True),
        sge.gfx.BackgroundLayer(
            nightsky_bottom_spr, 0, 600, -100010, xscroll_rate=0.25,
            yscroll_rate=0.25, repeat_left=True, repeat_right=True,
            repeat_down=True)]
    del nightsky_bottom_spr

backgrounds["nightsky"] = sge.gfx.Background(layers, sge.gfx.Color("#002"))

if not NO_BACKGROUNDS:
    layers = [
        sge.gfx.BackgroundLayer(
            sge.gfx.Sprite("bluemountain-middle", d, transparent=False), 0,
            -128, -100000, xscroll_rate=0.1, yscroll_rate=0.1,
            repeat_left=True, repeat_right=True),
        sge.gfx.BackgroundLayer(
            sge.gfx.Sprite("bluemountain-top", d, transparent=False), 0, -704,
            -100000, xscroll_rate=0.1, yscroll_rate=0.1, repeat_left=True,
            repeat_right=True, repeat_up=True),
        sge.gfx.BackgroundLayer(
            sge.gfx.Sprite("bluemountain-bottom", d, transparent=False), 0,
            448, -100000, xscroll_rate=0.1, yscroll_rate=0.1, repeat_left=True,
            repeat_right=True, repeat_down=True)]

backgrounds["bluemountain"] = sge.gfx.Background(layers,
                                                 sge.gfx.Color((86, 142, 206)))

castle_spr = sge.gfx.Sprite("castle", d)
castle_bottom_spr = sge.gfx.Sprite("castle-bottom", d, transparent=False)
for i in list(backgrounds.keys()):
    if not NO_BACKGROUNDS:
        layers = backgrounds[i].layers + [
            sge.gfx.BackgroundLayer(castle_spr, 0, -64, -99000,
                                    xscroll_rate=0.75, yscroll_rate=1,
                                    repeat_left=True, repeat_right=True,
                                    repeat_up=True),
            sge.gfx.BackgroundLayer(castle_bottom_spr, 0, 544, -99000,
                                    xscroll_rate=0.75, yscroll_rate=1,
                                    repeat_left=True, repeat_right=True,
                                    repeat_down=True)]

        backgrounds["{}_castle".format(i)] = sge.gfx.Background(
            layers, backgrounds[i].color)
    else:
        backgrounds["{}_castle".format(i)] = sge.gfx.Background(
            [], sge.gfx.Color("#221833"))
del castle_spr
del castle_bottom_spr

# Load fonts
print(_("Loading fonts..."))
chars = ([None] + [six.unichr(i) for i in six.moves.range(33, 127)] +
         ['\u2190', ' '] + [six.unichr(i) for i in six.moves.range(161, 384)])

font_sprite = sge.gfx.Sprite.from_tileset(
    os.path.join(DATA, "images", "misc", "font.png"), columns=16, rows=20,
    width=16, height=18)
font = sge.gfx.Font.from_sprite(font_sprite, chars, size=18)

font_small_sprite = sge.gfx.Sprite.from_tileset(
    os.path.join(DATA, "images", "misc", "font_small.png"), columns=16,
    rows=20, width=8, height=9)
font_small = sge.gfx.Font.from_sprite(font_small_sprite, chars, size=9)

font_big_sprite = sge.gfx.Sprite.from_tileset(
    os.path.join(DATA, "images", "misc", "font_big.png"), columns=16, rows=20,
    width=20, height=22)
font_big = sge.gfx.Font.from_sprite(font_big_sprite, chars, size=22)

# Load sounds
jump_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "jump.wav"))
bigjump_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "bigjump.wav"))
skid_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "skid.wav"), 50)
hurt_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "hurt.wav"))
kill_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "kill.wav"))
brick_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "brick.wav"))
coin_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "coin.wav"))
find_powerup_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "upgrade.wav"))
tuxdoll_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "tuxdoll.wav"))
s = sge.snd.Sound(os.path.join(DATA, "sounds", "ice_crack-0.wav"))
ice_crack_sounds = [
    s,
    sge.snd.Sound(os.path.join(DATA, "sounds", "ice_crack-1.wav"), parent=s),
    sge.snd.Sound(os.path.join(DATA, "sounds", "ice_crack-2.wav"), parent=s),
    sge.snd.Sound(os.path.join(DATA, "sounds", "ice_crack-3.wav"), parent=s)]
ice_shatter_sound = sge.snd.Sound(os.path.join(DATA, "sounds",
                                               "ice_shatter.wav"))
heal_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "heal.wav"))
shoot_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "shoot.wav"))
fire_dissipate_sound = sge.snd.Sound(os.path.join(DATA, "sounds",
                                                  "fire_dissipate.wav"))
icebullet_break_sound = sge.snd.Sound(os.path.join(DATA, "sounds",
                                                   "icebullet_break.wav"))
squish_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "squish.wav"))
stomp_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "stomp.wav"))
sizzle_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "sizzle.ogg"))
spring_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "spring.wav"))
rusty_spring_sound = sge.snd.Sound(os.path.join(DATA, "sounds",
                                                "rusty_spring.wav"))
kick_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "kick.wav"))
iceblock_bump_sound = sge.snd.Sound(os.path.join(DATA, "sounds",
                                                 "iceblock_bump.wav"))
icicle_shake_sound = sge.snd.Sound(os.path.join(DATA, "sounds",
                                                "icicle_shake.wav"))
icicle_crash_sound = sge.snd.Sound(os.path.join(DATA, "sounds",
                                                "icicle_crash.wav"))
explosion_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "explosion.wav"))
fall_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "fall.wav"))
yeti_gna_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "yeti_gna.wav"))
yeti_roar_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "yeti_roar.wav"))
pop_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "pop.wav"))
bell_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "bell.wav"))
pipe_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "pipe.ogg"))
warp_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "warp.wav"))
door_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "door.wav"))
door_shut_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "door_shut.wav"))
pause_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "select.ogg"))
select_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "select.ogg"))
confirm_sound = coin_sound
cancel_sound = pop_sound
error_sound = hurt_sound
type_sound = sge.snd.Sound(os.path.join(DATA, "sounds", "type.wav"))

# Load music
level_win_music = sge.snd.Music(os.path.join(DATA, "music", "leveldone.ogg"))
loaded_music["leveldone.ogg"] = level_win_music

# Create objects
coin_animation = sge.dsp.Object(0, 0, sprite=coin_sprite, visible=False,
                                tangible=False)
bonus_animation = sge.dsp.Object(0, 0, sprite=bonus_empty_sprite,
                                 visible=False, tangible=False)
lava_animation = sge.dsp.Object(0, 0, sprite=lava_body_sprite, visible=False,
                                tangible=False)
goal_animation = sge.dsp.Object(0, 0, sprite=goal_sprite, visible=False,
                                tangible=False)

# Create rooms
if LEVEL:
    sge.game.start_room = LevelTester.load(LEVEL, True)
    if sge.game.start_room is None:
        sys.exit()
elif RECORD:
    sge.game.start_room = LevelRecorder.load(RECORD, True)
    if sge.game.start_room is None:
        sys.exit()
else:
    sge.game.start_room = TitleScreen.load(
        os.path.join("special", "title_screen.tmx"), True)

sge.game.mouse.visible = False

if not os.path.exists(CONFIG):
    os.makedirs(CONFIG)

# Save error messages to a text file (so they aren't lost).
if not PRINT_ERRORS:
    stderr = os.path.join(CONFIG, "stderr.txt")
    if not os.path.isfile(stderr) or os.path.getsize(stderr) > 1000000:
        sys.stderr = open(stderr, 'w')
    else:
        sys.stderr = open(stderr, 'a')
    dt = datetime.datetime.now()
    sys.stderr.write("\n{}-{}-{} {}:{}:{}\n".format(
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
    del dt

try:
    with open(os.path.join(CONFIG, "config.json")) as f:
        cfg = json.load(f)
except (IOError, OSError, ValueError):
    cfg = {}
finally:
    cfg_version = cfg.get("version", 0)

    fullscreen = cfg.get("fullscreen", fullscreen)
    sge.game.fullscreen = fullscreen
    scale_method = cfg.get("scale_method", scale_method)
    sge.game.scale_method = scale_method
    sound_enabled = cfg.get("sound_enabled", sound_enabled)
    music_enabled = cfg.get("music_enabled", music_enabled)
    stereo_enabled = cfg.get("stereo_enabled", stereo_enabled)
    fps_enabled = cfg.get("fps_enabled", fps_enabled)
    joystick_threshold = cfg.get("joystick_threshold", joystick_threshold)
    xsge_gui.joystick_threshold = joystick_threshold

    if cfg_version >= 1:
        keys_cfg = cfg.get("keys", {})
        left_key = keys_cfg.get("left", left_key)
        right_key = keys_cfg.get("right", right_key)
        up_key = keys_cfg.get("up", up_key)
        down_key = keys_cfg.get("down", down_key)
        jump_key = keys_cfg.get("jump", jump_key)
        action_key = keys_cfg.get("action", action_key)
        sneak_key = keys_cfg.get("sneak", sneak_key)
        menu_key = keys_cfg.get("menu", menu_key)
        pause_key = keys_cfg.get("pause", pause_key)

        js_cfg = cfg.get("joystick", {})
        left_js = [[tuple(j) for j in js]
                   for js in js_cfg.get("left", left_js)]
        right_js = [[tuple(j) for j in js]
                    for js in js_cfg.get("right", right_js)]
        up_js = [[tuple(j) for j in js] for js in js_cfg.get("up", up_js)]
        down_js = [[tuple(j) for j in js]
                   for js in js_cfg.get("down", down_js)]
        jump_js = [[tuple(j) for j in js]
                   for js in js_cfg.get("jump", jump_js)]
        action_js = [[tuple(j) for j in js]
                     for js in js_cfg.get("action", action_js)]
        sneak_js = [[tuple(j) for j in js]
                    for js in js_cfg.get("sneak", sneak_js)]
        menu_js = [[tuple(j) for j in js]
                   for js in js_cfg.get("menu", menu_js)]
        pause_js = [[tuple(j) for j in js]
                    for js in js_cfg.get("pause", pause_js)]
    else:
        keys_cfg = cfg.get("keys", {})
        if "left" in keys_cfg:
            left_key = [keys_cfg["left"]]
        if "right" in keys_cfg:
            right_key = [keys_cfg["right"]]
        if "up" in keys_cfg:
            up_key = [keys_cfg["up"]]
        if "down" in keys_cfg:
            down_key = [keys_cfg["down"]]
        if "jump" in keys_cfg:
            jump_key = [keys_cfg["jump"]]
        if "action" in keys_cfg:
            action_key = [keys_cfg["action"]]
        if "sneak" in keys_cfg:
            sneak_key = [keys_cfg["sneak"]]
        if "pause" in keys_cfg:
            pause_key = [keys_cfg["pause"]]

        js_cfg = cfg.get("joystick", {})
        if "left" in js_cfg:
            left_js = [[tuple(j)] for j in js_cfg["left"]]
        if "right" in js_cfg:
            right_js = [[tuple(j)] for j in js_cfg["right"]]
        if "up" in js_cfg:
            up_js = [[tuple(j)] for j in js_cfg["up"]]
        if "down" in js_cfg:
            down_js = [[tuple(j)] for j in js_cfg["down"]]
        if "jump" in js_cfg:
            jump_js = [[tuple(j)] for j in js_cfg["jump"]]
        if "action" in js_cfg:
            action_js = [[tuple(j)] for j in js_cfg["action"]]
        if "sneak" in js_cfg:
            sneak_js = [[tuple(j)] for j in js_cfg["sneak"]]
        if "pause" in js_cfg:
            pause_js = [[tuple(j)] for j in js_cfg["pause"]]

    set_gui_controls()

try:
    with open(os.path.join(CONFIG, "save_slots.json")) as f:
        loaded_slots = json.load(f)
except (IOError, OSError, ValueError):
    pass
else:
    for i in six.moves.range(min(len(loaded_slots), len(save_slots))):
        save_slots[i] = loaded_slots[i]


if __name__ == '__main__':
    print(_("Starting game..."))

    if HAVE_TK:
        tkwindow = Tk()
        tkwindow.withdraw()

    try:
        sge.game.start()
    finally:
        write_to_disk()
        shutil.rmtree(DATA)
