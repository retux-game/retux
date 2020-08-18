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
Constant defs for ReTux.  Be sure to call :func:`init` after importing.
"""


import gettext
import os


DATA = tempfile.mkdtemp("retux-data")
CONFIG = os.environ.get(
    "XDG_CONFIG_HOME",
    os.path.join(os.path.expanduser("~"), ".config", "retux"))

SCREEN_SIZE = [800, 448]
TILE_SIZE = 32
FPS = 56
DELTA_MIN = FPS / 2
DELTA_MAX = FPS * 4
TRANSITION_TIME = 750

DEFAULT_LEVELSET = "retux.json"
DEFAULT_LEVEL_TIME_BONUS = 90000

Z_BACK = 0
Z_MIDDLE = 1
Z_ITEMS = 2
Z_BOSS = 3
Z_ENEMIES = 4
Z_PLAYER = 5
Z_FRONT = 6

TUX_ORIGIN_X = 28
TUX_ORIGIN_Y = 16
TUX_KICK_TIME = 10

GRAVITY = 0.4

PLAYER_SKID_THRESHOLD = 3
PLAYER_WALK_FRAMES_PER_PIXEL = 2 / 17
PLAYER_RUN_FRAMES_PER_PIXEL = 1 / 10
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
WIN_COUNT_POINTS_MAX = FPS
WIN_COUNT_TIME_MAX = 5 * FPS
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


def init(prgdir):
    # Initialize the module.  Pass the program directory to the
    # ``prgdir`` argument; should be ``os.path.dirname(__file__)`` from
    # the main script.
    global PRINT_ERRORS
    global DELTA
    global LEVEL
    global RECORD
    global NO_BACKGROUNDS
    global NO_HUD
    global GOD

    dirs = [os.path.join(prgdir, "data"), os.path.join(CONFIG, "data")]

    gettext.install("retux", os.path.abspath(os.path.join(dirs[0], "locale")))

    parser = argparse.ArgumentParser(prog="ReTux")
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__,
        help=_("Output version information and exit."))
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

    gettext.install("retux", os.path.abspath(os.path.join(DATA, "locale")))

    if args.lang:
        lang = gettext.translation(
            "retux", os.path.abspath(os.path.join(DATA, "locale")),
            [args.lang])
        lang.install()
