#!/usr/bin/env python3

# reTux
# Copyright (C) 2015 Julian Marchant <onpon4@riseup.net>
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

__version__ = "0.1a1"

import os
import math
import json
import warnings
import weakref

import six
import sge
import xsge_gui
import xsge_path
import xsge_physics
import xsge_tmx

DATA = os.path.join(os.path.dirname(__file__), "data")

SCREEN_SIZE = [800, 448]
TILE_SIZE = 32
FPS = 60

DEFAULT_LEVEL_TIME_BONUS = 30000

TUX_ORIGIN_X = 28
TUX_ORIGIN_Y = 16
TUX_KICK_TIME = 5

PLAYER_WALK_SPEED = 2
PLAYER_RUN_SPEED = 4
PLAYER_MAX_SPEED = 5
PLAYER_ACCELERATION = 0.2
PLAYER_AIR_ACCELERATION = 0.1
PLAYER_FRICTION = 0.17
PLAYER_AIR_FRICTION = 0.03
PLAYER_JUMP_HEIGHT = 4 * TILE_SIZE + 2
PLAYER_RUN_JUMP_HEIGHT = 5 * TILE_SIZE + 2
PLAYER_STOMP_HEIGHT = TILE_SIZE / 2
PLAYER_GRAVITY = 0.25
PLAYER_FALL_SPEED = 5
PLAYER_SLIDE_ACCEL = 0.3
PLAYER_SLIDE_SPEED = 1
PLAYER_WALK_FRAMES_PER_PIXEL = 2 / 17
PLAYER_RUN_IMAGE_SPEED = 0.25
PLAYER_HITSTUN = 120
PLAYER_DIE_HEIGHT = 6 * TILE_SIZE
PLAYER_DIE_FALL_SPEED = 8

# Using a kinematic equation: v[f]^2 = v[i]^2 + 2ad
PLAYER_JUMP_SPEED = math.sqrt(2 * PLAYER_GRAVITY * PLAYER_JUMP_HEIGHT)
PLAYER_RUN_JUMP_SPEED = math.sqrt(2 * PLAYER_GRAVITY * PLAYER_RUN_JUMP_HEIGHT)
PLAYER_STOMP_SPEED = math.sqrt(2 * PLAYER_GRAVITY * PLAYER_STOMP_HEIGHT)
PLAYER_DIE_SPEED = math.sqrt(2 * PLAYER_GRAVITY * PLAYER_DIE_HEIGHT)

MAX_HP = 5
TIMER_FRAMES = 40
HEAL_COINS = 20

CEILING_LAX = 10
STOMP_LAX = 8

BLOCK_HIT_SPEED = 2
BLOCK_HIT_GRAVITY = 0.25
COIN_COLLECT_TIME = 30
COIN_COLLECT_SPEED = 2
ITEM_SPAWN_SPEED = 1

SECOND_POINTS = 100
COIN_POINTS = 100

CAMERA_SPEED_FACTOR = 1 / 2
CAMERA_OFFSET_FACTOR = 8
CAMERA_MARGIN_TOP = 4 * TILE_SIZE
CAMERA_MARGIN_BOTTOM = 5 * TILE_SIZE

WARP_LAX = 12
WARP_SPEED = 1.5

ENEMY_WALK_SPEED = 1
ENEMY_GRAVITY = 0.5
ENEMY_FALL_SPEED = 5
ENEMY_SLIDE_SPEED = 0.3
ENEMY_HIT_BELOW_HEIGHT = TILE_SIZE * 3 / 4
ENEMY_HIT_BELOW_SPEED = math.sqrt(2 * PLAYER_GRAVITY * ENEMY_HIT_BELOW_HEIGHT)
ENEMY_KILL_POINTS = 50
KICK_UP_HEIGHT = 5.5 * TILE_SIZE
KICK_UP_SPEED = math.sqrt(2 * ENEMY_GRAVITY * KICK_UP_HEIGHT)
ICEBLOCK_FALL_SPEED = 10
ICEBLOCK_FRICTION = 0.1
ICEBLOCK_DASH_SPEED = 7

COINBRICK_COINS = 20
COINBRICK_DECAY_TIME = 25

ENEMY_ACTIVE_RANGE = 32
TILE_ACTIVE_RANGE = 128
DEATHZONE = 2 * TILE_SIZE

DEATH_FADE_TIME = 3000
DEATH_RESTART_WAIT = FPS

WIN_COUNT_START_TIME = 120
WIN_COUNT_CONTINUE_TIME = 60
WIN_COUNT_MULT = 100
WIN_COUNT_AMOUNT = 1
WIN_FINISH_DELAY = 120

TITLE_MUSIC = "theme.ogg"
BOSS_MUSIC = "bossattack.ogg"
FINAL_BOSS_MUSIC = "treeboss.ogg"

left_key = ["left"]
right_key = ["right"]
up_key = ["up"]
down_key = ["down"]
jump_key = ["space"]
action_key = ["ctrl_left"]
sneak_key = ["shift_left"]

backgrounds = {}
loaded_music = {}
tux_grab_sprites = {}

levels = []
current_level = None
current_areas = {}
main_area = None

score = 0


class Game(sge.Game):

    def event_mouse_button_press(self, button):
        if button == "middle":
            self.event_close()

    def event_close(self):
        self.mouse.visible = True
        m = "Are you sure you want to quit?"
        if xsge_gui.show_message(message=m, buttons=["No", "Yes"], default=0):
            self.end()
        self.mouse.visible = False

    def event_paused_close(self):
        self.event_close()


class Level(sge.Room):

    """Handles levels."""

    def __init__(self, objects=(), width=None, height=None, views=None,
                 background=None, background_x=0, background_y=0,
                 bgname=None, music=None, time_bonus=DEFAULT_LEVEL_TIME_BONUS,
                 spawn=None, timeline=None):
        self.fname = None
        self.music = music
        self.time_bonus = time_bonus
        self.spawn = spawn
        self.points = 0
        self.finished = False
        self.timeline = {}
        self.timeline_objects = {}
        self.timeline_step = 0
        self.warps = []

        if bgname is not None:
            background = backgrounds.get(bgname, background)

        if timeline is not None:
            fname = os.path.join(DATA, "timelines", timeline)
            with open(fname, 'r') as f:
                jt = json.load(f)

            for i in jt:
                self.timeline[eval(i)] = jt[i]

        super(Level, self).__init__(objects, width, height, views, background,
                                    background_x, background_y)

    def add_timeline_object(self, obj):
        if obj.ID is not None:
            self.timeline_objects[obj.ID] = weakref.ref(obj)

    def add_points(self, x):
        if not self.finished:
            self.points += x

    def show_hud(self):
        if self.points:
            score_text = "{}+{}".format(score, self.points)
        else:
            score_text = str(score)
        text = "Score\n{}\n\nTime {}\n{}".format(
            score_text, "Bonus" if self.time_bonus >= 0 else "Penalty",
            abs(self.time_bonus))
        sge.game.project_text(font, text, sge.game.width / 2, 0,
                              color=sge.Color("white"), halign="center")

    def die(self):
        global current_areas
        current_areas = {}
        self.death_time = DEATH_FADE_TIME
        if "timer" in self.alarms:
            del self.alarms["timer"]
        sge.Music.clear_queue()
        sge.Music.stop(DEATH_FADE_TIME)

    def event_room_start(self):
        self.add(coin_animation)
        self.add(bonus_animation)
        self.event_room_resume()

    def event_room_resume(self):
        global main_area

        self.won = False
        self.win_count_points = False
        self.win_count_time = False
        self.death_time = None
        self.alarms["timer"] = TIMER_FRAMES
        play_music(self.music)

        if main_area is None:
            main_area = self.fname

        for obj in self.objects:
            if isinstance(obj, Warp) and not obj in self.warps:
                self.warps.append(obj)

        del_warps = []
        for warp in self.warps:
            if warp not in self.objects:
                del_warps.append(warp)
        for warp in del_warps:
            self.warps.remove(warp)

        if self.spawn is not None:
            players = []
            spawn_point = None
            for obj in self.objects:
                if isinstance(obj, Player):
                    players.append(obj)
                elif isinstance(obj, WarpSpawn):
                    if obj.spawn_id == self.spawn:
                        spawn_point = obj

            if spawn_point is not None:
                for player in players:
                    player.x = spawn_point.x
                    player.y = spawn_point.y
                    if player.view is not None:
                        player.view.x = player.x - player.view.width / 2
                        player.view.y = player.y - player.view.height / 2

                    if isinstance(spawn_point, WarpSpawn):
                        player.visible = False
                        player.tangible = False
                        player.warping = True
                        spawn_point.follow_start(player, WARP_SPEED)

    def event_step(self, time_passed, delta_mult):
        global score
        global current_areas
        global main_area

        self.show_hud()

        # Timeline events
        t_keys = sorted(self.timeline.keys())
        for i in t_keys:
            if i <= self.timeline_step:
                for command in timeline[i]:
                    command = command.split(maxsplit=1)
                    if command:
                        if len(command) >= 2:
                            command, arg = command[:2]
                        else:
                            command = command[0]
                            arg = ""

                        if command == "setattr":
                            args = arg.split(maxsplit=2)
                            if len(args) >= 2:
                                if len(args) >= 3:
                                    obj, name, value = args[:3]
                                else:
                                    obj = None
                                    name, value = args[:2]

                                try:
                                    value = int(value)
                                except ValueError:
                                    try:
                                        value = float(value)
                                    except ValueError:
                                        pass

                                if obj is None:
                                    setattr(self, name, value)
                                elif obj in self.timeline_objects:
                                    setattr(self.timeline_objects[obj], name,
                                            value)
                del self.timeline[i]
            else:
                break

        self.timeline_step += delta_mult

        if self.death_time is not None:
            a = int(255 * (DEATH_FADE_TIME - self.death_time) / DEATH_FADE_TIME)
            sge.game.project_rectangle(0, 0, sge.game.width, sge.game.height,
                                       fill=sge.Color((0, 0, 0, min(a, 255))))

            if self.death_time < 0:
                self.death_time = None
                self.alarms["death"] = DEATH_RESTART_WAIT
            else:
                self.death_time -= time_passed
        elif "death" in self.alarms:
            sge.game.project_rectangle(0, 0, sge.game.width, sge.game.height,
                                       fill=sge.Color("black"))

        if self.won:
            if self.win_count_points:
                if self.points:
                    amt = int(math.copysign(
                        min(WIN_COUNT_AMOUNT * delta_mult * WIN_COUNT_MULT,
                            abs(self.points)),
                        self.points))
                    score += amt
                    self.points -= amt
                    coin_sound.play()
                else:
                    self.win_count_points = False
                    self.alarms["win_count_time"] = WIN_COUNT_CONTINUE_TIME
            elif self.win_count_time:
                if self.time_bonus:
                    amt = int(math.copysign(
                        min(WIN_COUNT_AMOUNT * delta_mult * WIN_COUNT_MULT,
                            abs(self.time_bonus)),
                        self.time_bonus))
                    score += amt
                    self.time_bonus -= amt
                    coin_sound.play()
                else:
                    self.win_count_time = False
                    self.alarms["win"] = WIN_FINISH_DELAY
            elif (not level_win_music.playing and
                  "win_count_points" not in self.alarms and
                  "win_count_time" not in self.alarms and
                  "win" not in self.alarms):
                current_areas = {}
                main_area = None

                # TODO: Next level or worldmap
                sge.game.end()

    def event_paused_step(self, time_passed, delta_mult):
        self.show_hud()

    def event_alarm(self, alarm_id):
        global score

        if alarm_id == "timer":
            self.time_bonus -= SECOND_POINTS
            self.alarms["timer"] = TIMER_FRAMES
        elif alarm_id == "death":
            if main_area is not None:
                r = Level.load(main_area)
                r.time_bonus = self.time_bonus
                r.start()
        elif alarm_id == "win_count_points":
            self.win_count_points = True
        elif alarm_id == "win_count_time":
            self.win_count_time = True

    def event_key_press(self, key, char):
        if self.death_time is not None or "death" in self.alarms:
            sge.Music.stop()
            self.alarms["death"] = 0
        else:
            if key == "f11":
                sge.game.fullscreen = not sge.game.fullscreen
            elif key == "escape":
                sge.game.event_close()
            elif key in ("enter", "p"):
                if not self.won:
                    sge.game.pause()

    def event_paused_key_press(self, key, char):
        if key in ("enter", "p"):
            sge.game.unpause()
        else:
            self.event_key_press(key, char)

    @classmethod
    def load(cls, fname):
        if fname in current_areas:
            return current_areas[fname]
        else:
            r = xsge_tmx.load(os.path.join(DATA, "levels", fname), cls=cls,
                              types=TYPES)
            r.fname = fname
            current_areas[fname] = r
            return r


class Tile(sge.Object):

    # FIXME: It would be very nice to have this optimization, but it's
    # causing objects to fall through the floor ever since I changed
    # movement from event_step to event_begin_step in InteractiveObject.
    def event_step_null(self, time_passed, delta_mult):
        for view in sge.game.current_room.views:
            if (self.bbox_left <= view.x + view.width + TILE_ACTIVE_RANGE and
                    self.bbox_right >= view.x - TILE_ACTIVE_RANGE and
                    self.bbox_top <= (view.y + view.height +
                                      TILE_ACTIVE_RANGE) and
                    self.bbox_bottom >= view.y - TILE_ACTIVE_RANGE):
                self.tangible = True
                break
        else:
            self.tangible = False


class SolidLeft(xsge_physics.SolidLeft, Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SolidLeft, self).__init__(*args, **kwargs)


class SolidRight(xsge_physics.SolidRight, Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SolidRight, self).__init__(*args, **kwargs)


class SolidTop(xsge_physics.SolidTop, Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SolidTop, self).__init__(*args, **kwargs)


class SolidBottom(xsge_physics.SolidBottom, Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SolidBottom, self).__init__(*args, **kwargs)


class Solid(xsge_physics.Solid, Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(Solid, self).__init__(*args, **kwargs)


class SlopeTopLeft(xsge_physics.SlopeTopLeft, Tile):

    xsticky_top = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SlopeTopLeft, self).__init__(*args, **kwargs)


class SlopeTopRight(xsge_physics.SlopeTopRight, Tile):

    xsticky_top = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SlopeTopRight, self).__init__(*args, **kwargs)


class SlopeBottomLeft(xsge_physics.SlopeBottomLeft, Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SlopeBottomLeft, self).__init__(*args, **kwargs)


class SlopeBottomRight(xsge_physics.SlopeBottomRight, Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(SlopeBottomRight, self).__init__(*args, **kwargs)


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


class Death(Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(Death, self).__init__(*args, **kwargs)


class LevelEnd(Tile):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("visible", False)
        kwargs.setdefault("checks_collisions", False)
        super(LevelEnd, self).__init__(*args, **kwargs)


class Player(xsge_physics.Collider):

    @property
    def warping(self):
        return self.__warping

    @warping.setter
    def warping(self, value):
        self.__warping = value
        if self.held_object is not None:
            if value:
                self.held_object.x = -666
                self.held_object.y = -666
            else:
                self.held_object.x = self.x + self.held_object.image_origin_x
                self.held_object.y = self.y

    def __init__(self, x, y, z=0, sprite=None, visible=True, active=True,
                 checks_collisions=True, tangible=True, bbox_x=-13, bbox_y=2,
                 bbox_width=26, bbox_height=30, regulate_origin=True,
                 collision_ellipse=False, collision_precise=False, xvelocity=0,
                 yvelocity=0, xacceleration=0, yacceleration=0,
                 xdeceleration=0, ydeceleration=0, image_index=0,
                 image_origin_x=None, image_origin_y=None, image_fps=None,
                 image_xscale=1, image_yscale=1, image_rotation=0,
                 image_alpha=255, image_blend=None, ID="player", player=0,
                 human=True, lose_on_death=True):
        self.ID = ID
        self.player = player
        self.human = human
        self.lose_on_death = lose_on_death

        self.held_object = None
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.jump_pressed = False
        self.action_pressed = False
        self.sneak_pressed = False
        self.hp = MAX_HP
        self.coins = 0
        self.hitstun = False
        self.warping = False
        self.facing = 1
        self.view = None

        x += TUX_ORIGIN_X
        y += TUX_ORIGIN_Y
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
            self.left_pressed = sge.keyboard.get_pressed(left_key[self.player])
            self.right_pressed = sge.keyboard.get_pressed(
                right_key[self.player])
            self.up_pressed = sge.keyboard.get_pressed(up_key[self.player])
            self.down_pressed = sge.keyboard.get_pressed(down_key[self.player])
            self.jump_pressed = sge.keyboard.get_pressed(jump_key[self.player])
            self.action_pressed = sge.keyboard.get_pressed(
                action_key[self.player])
            self.sneak_pressed = sge.keyboard.get_pressed(
                sneak_key[self.player])

    def jump(self):
        if not self.warping and (self.on_floor or self.was_on_floor):
            if abs(self.xvelocity) >= PLAYER_RUN_SPEED:
                self.yvelocity = -PLAYER_RUN_JUMP_SPEED
            else:
                self.yvelocity = -PLAYER_JUMP_SPEED
            self.on_floor = []
            self.was_on_floor = []
            jump_sound.play()

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

    def stomp_jump(self, other):
        if self.jump_pressed:
            self.yvelocity = -PLAYER_JUMP_SPEED
        else:
            self.yvelocity = -PLAYER_STOMP_SPEED
        T = math.floor(other.bbox_top / TILE_SIZE) * TILE_SIZE
        self.move_y(T - self.bbox_bottom)

    def hurt(self):
        if not self.hitstun:
            self.hp -= 1
            if self.hp <= 0:
                self.kill()
            else:
                hurt_sound.play()
                self.hitstun = True
                self.image_alpha = 128
                self.alarms["hitstun"] = PLAYER_HITSTUN

    def kill(self, show_fall=True):
        if self.held_object is not None:
            self.held_object.drop()
        kill_sound.play()
        if show_fall:
            DeadMan.create(self.x, self.y, 100000, sprite=tux_die_sprite,
                           yvelocity=-PLAYER_DIE_SPEED)

        if self.lose_on_death and not sge.game.current_room.won:
            sge.game.current_room.die()

        self.destroy()

    def win_level(self):
        self.human = False
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.jump_pressed = False
        self.action_pressed = False
        self.sneak_pressed = True
        self.jump_release()

        if self.xvelocity >= 0:
            self.right_pressed = True
        else:
            self.left_pressed = True

        if "timer" in sge.game.current_room.alarms:
            del sge.game.current_room.alarms["timer"]

        sge.game.current_room.won = True
        sge.game.current_room.alarms["win_count_points"] = WIN_COUNT_START_TIME
        sge.Music.clear_queue()
        sge.Music.stop()
        level_win_music.play()

    def pickup(self, other):
        if self.held_object is None:
            other.visible = False
            self.held_object = other
            return True
        else:
            return False

    def drop_object(self):
        if self.held_object is not None:
            self.held_object.visible = True
            self.held_object = None

    def kick_object(self):
        self.drop_object()
        kick_sound.play()
        self.alarms["fixed_sprite"] = TUX_KICK_TIME
        self.sprite = tux_kick_sprite

    def show_hud(self):
        y = 0
        sge.game.project_text(font, "Tux", 0, y, color=sge.Color("white"))

        x = 0
        y += 36
        for i in six.moves.range(MAX_HP):
            if self.hp >= i + 1:
                sge.game.project_sprite(heart_full_sprite, 0, x, y)
            else:
                sge.game.project_sprite(heart_empty_sprite, 0, x, y)
            x += heart_empty_sprite.width

        y += 18
        sge.game.project_sprite(coin_icon_sprite, coin_animation.image_index,
                                0, y)
        sge.game.project_text(font, "x{}".format(self.coins), 16, y,
                              color=sge.Color("white"))

    def get_grab_sprite(self, body_sprite, arms_sprite=None):
        if arms_sprite is None: arms_sprite = tux_arms_grab_sprite

        if self.held_object is not None:
            obj_sprite = self.held_object.sprite
            obj_image_index = self.held_object.image_index

            i = (id(body_sprite), id(obj_sprite), obj_image_index)
            if i in tux_grab_sprites:
                return tux_grab_sprites[i]
            else:
                origin_x = body_sprite.origin_x
                origin_y = body_sprite.origin_y
                width = body_sprite.width
                height = body_sprite.height

                if obj_sprite.origin_x < 0:
                    origin_x -= obj_sprite.origin_x
                    width -= obj_sprite.origin_x
                width = max(width, origin_x + obj_sprite.width)

                top = body_sprite.origin_y - obj_sprite.origin_y
                if top < 0:
                    origin_y -= top
                    height -= top
                height = max(height, top + obj_sprite.height)

                grab_sprite = sge.Sprite(width=width, height=height,
                                         origin_x=origin_x, origin_y=origin_y)
                for j in six.moves.range(1, body_sprite.frames):
                    grab_sprite.append_frame()
                grab_sprite.draw_lock()
                for j in six.moves.range(grab_sprite.frames):
                    grab_sprite.draw_sprite(obj_sprite, obj_image_index,
                                            origin_x + obj_sprite.origin_x,
                                            origin_y, j)
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

    def event_create(self):
        sge.game.current_room.add_timeline_object(self)

        self.last_x = self.x
        self.last_y = self.y
        self.on_slope = self.get_bottom_touching_slope()
        self.on_floor = self.get_bottom_touching_wall() + self.on_slope
        self.was_on_floor = self.on_floor

        self.view = sge.game.current_room.views[self.player]
        self.view.x = self.x - self.view.width / 2
        self.view.y = self.y - self.view.height / 2

    def event_update_position(self, delta_mult):
        super(Player, self).event_update_position(delta_mult)

        held_object = self.held_object
        if not self.warping and held_object is not None:
            target_x = self.x + held_object.image_origin_x
            target_y = self.y
            if self.image_xscale < 0:
                target_x -= held_object.sprite.width
            if isinstance(held_object, xsge_physics.Collider):
                held_object.move_x(target_x - held_object.x)
                held_object.move_y(target_y - held_object.y)
            else:
                held_object.x = target_x
                held_object.y = target_y

    def event_begin_step(self, time_passed, delta_mult):
        if not self.warping:
            self.refresh_input()

            h_control = self.right_pressed - self.left_pressed
            current_h_movement = (self.xvelocity > 0) - (self.xvelocity < 0)

            self.xacceleration = 0
            self.yacceleration = 0
            self.xdeceleration = 0

            if h_control:
                self.facing = h_control
                self.image_xscale = h_control * abs(self.image_xscale)
                if (abs(self.xvelocity) < PLAYER_MAX_SPEED and
                        (not self.sneak_pressed or
                         abs(self.xvelocity) < PLAYER_WALK_SPEED)):
                    if self.on_floor or self.was_on_floor:
                        self.xacceleration = PLAYER_ACCELERATION * h_control
                    else:
                        self.xacceleration = PLAYER_AIR_ACCELERATION * h_control
                else:
                    if self.sneak_pressed:
                        if self.on_floor or self.was_on_floor:
                            dc = PLAYER_FRICTION
                        else:
                            dc = PLAYER_AIR_FRICTION

                        if self.xvelocity - dc * delta_mult > PLAYER_WALK_SPEED:
                            self.xdeceleration = dc
                        else:
                            self.xvelocity = (PLAYER_WALK_SPEED *
                                              current_h_movement)
                    else:
                        self.xvelocity = PLAYER_MAX_SPEED * current_h_movement

            if current_h_movement and h_control != current_h_movement:
                if self.on_floor or self.was_on_floor:
                    self.xdeceleration = PLAYER_FRICTION
                else:
                    self.xdeceleration = PLAYER_AIR_FRICTION

            if not self.on_floor and not self.was_on_floor:
                if self.yvelocity < PLAYER_FALL_SPEED:
                    self.yacceleration = PLAYER_GRAVITY
                else:
                    self.yvelocity = PLAYER_FALL_SPEED
            elif self.on_slope:
                self.yvelocity = (PLAYER_SLIDE_SPEED *
                                  (self.on_slope[0].bbox_height /
                                   self.on_slope[0].bbox_width))

    def event_step(self, time_passed, delta_mult):
        if self.warping:
            self.event_step_warp(time_passed, delta_mult)
        else:
            self.event_step_normal(time_passed, delta_mult)

        # Move view
        view_target_x = (self.x - self.view.width / 2 +
                         self.xvelocity * CAMERA_OFFSET_FACTOR)
        if abs(view_target_x - self.view.x) > 0.5:
            self.view.x += ((view_target_x - self.view.x) *
                            CAMERA_SPEED_FACTOR)
        else:
            self.view.x = view_target_x

        view_min_y = self.y - self.view.height + CAMERA_MARGIN_BOTTOM
        view_max_y = self.y - CAMERA_MARGIN_TOP
        if self.view.y < view_min_y:
            self.view.y = view_min_y
        elif self.view.y > view_max_y:
            self.view.y = view_max_y

        self.last_x = self.x
        self.last_y = self.y

        while self.coins >= HEAL_COINS:
            self.coins -= HEAL_COINS
            self.hp += 1
            heal_sound.play()

        self.hp = min(self.hp, MAX_HP)

        self.show_hud()

    def event_step_normal(self, time_passed, delta_mult):
        on_floor = self.get_bottom_touching_wall()
        self.on_slope = self.get_bottom_touching_slope() if not on_floor else []
        self.was_on_floor = self.on_floor
        self.on_floor = on_floor + self.on_slope
        h_control = self.right_pressed - self.left_pressed
        v_control = self.down_pressed - self.up_pressed

        for block in self.on_floor:
            if block in self.was_on_floor and isinstance(block, HurtTop):
                self.hurt()

        # Set image
        if "fixed_sprite" not in self.alarms:
            hands_free = (self.held_object is None)

            if self.on_floor and self.was_on_floor:
                xdiff = self.x - self.last_x
                speed = (math.hypot(abs(xdiff), abs(self.y - self.last_y)) /
                         delta_mult)
                xm = (xdiff > 0) - (xdiff < 0)
                if speed > 0:
                    if xm != self.facing:
                        skidding = skid_sound.playing
                        s = speed + self.xdeceleration * delta_mult
                        if (not skidding and h_control and
                                s >= PLAYER_RUN_SPEED):
                            skidding = True
                            skid_sound.play()
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
                                abs(self.xvelocity) < PLAYER_RUN_SPEED):
                            if xm == self.facing:
                                if hands_free:
                                    self.sprite = tux_walk_sprite
                                else:
                                    self.sprite = self.get_grab_sprite(
                                        tux_body_walk_sprite)
                            else:
                                if hands_free:
                                    self.sprite = tux_walk_reverse_sprite
                                else:
                                    self.sprite = self.get_grab_sprite(
                                        tux_body_walk_reverse_sprite)

                            self.image_speed = (speed *
                                                PLAYER_WALK_FRAMES_PER_PIXEL)
                        else:
                            if hands_free:
                                self.sprite = tux_run_sprite
                            else:
                                self.sprite = self.get_grab_sprite(
                                    tux_body_run_sprite)

                            self.image_speed = PLAYER_RUN_IMAGE_SPEED
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

        # Enter warp pipes
        if h_control > 0 and self.xvelocity >= 0:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "right" and self.bbox_right == warp.x and
                        abs(self.y - warp.y) < WARP_LAX):
                    warp.warp(self)
        elif h_control < 0 and self.xvelocity <= 0:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "left" and self.bbox_left == warp.x and
                        abs(self.y - warp.y) < WARP_LAX):
                    warp.warp(self)

        if v_control > 0 and self.yvelocity >= 0:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "down" and self.bbox_bottom == warp.y and
                        abs(self.x - warp.x) < WARP_LAX):
                    warp.warp(self)
        elif v_control < 0 and self.yvelocity <= 0:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "up" and self.bbox_top == warp.y and
                        abs(self.x - warp.x) < WARP_LAX):
                    warp.warp(self)

        # Prevent moving off-screen to the right or left
        if self.bbox_left < 0:
            self.bbox_left = 0
        elif self.bbox_right > sge.game.current_room.width:
            self.bbox_right = sge.game.current_room.width

        # Off-screen death
        if self.bbox_top > sge.game.current_room.height + DEATHZONE:
            self.kill(False)

    def event_step_warp(self, time_passed, delta_mult):
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
            if hands_free:
                self.sprite = tux_jump_sprite
            else:
                self.sprite = self.get_grab_sprite(tux_body_jump_sprite)

    def event_paused_step(self, time_passed, delta_mult):
        self.show_hud()

    def event_alarm(self, alarm_id):
        if alarm_id == "hitstun":
            self.hitstun = False
            self.image_alpha = 255

    def event_key_press(self, key, char):
        if self.human:
            if key == jump_key[self.player]:
                self.jump()
            elif key == action_key[self.player]:
                self.action()

    def event_key_release(self, key):
        if self.human:
            if key == jump_key[self.player]:
                self.jump_release()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, Death):
            self.kill()
        elif isinstance(other, LevelEnd):
            self.win_level()
            other.destroy()
        elif isinstance(other, InteractiveObject):
            if (ydirection == 1 or
                    (xdirection and not ydirection and
                     self.bbox_bottom - other.bbox_top <= STOMP_LAX) or
                    (xdirection and not self.on_floor and self.yvelocity > 0)):
                other.stomp(self)
            elif xdirection or ydirection:
                other.touch(self)

    def event_physics_collision_left(self, other, move_loss):
        for block in self.get_left_touching_wall():
            if isinstance(block, HurtRight):
                self.hurt()

        if isinstance(other, xsge_physics.SolidRight):
            self.xvelocity = 0

        if self.left_pressed:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "left" and self.bbox_left == warp.x and
                        abs(self.y - warp.y) < WARP_LAX):
                    self.image_speed = WARP_SPEED * PLAYER_WALK_FRAMES_PER_PIXEL
                    warp.warp(self)

    def event_physics_collision_right(self, other, move_loss):
        for block in self.get_right_touching_wall():
            if isinstance(block, HurtLeft):
                self.hurt()

        if isinstance(other, xsge_physics.SolidLeft):
            self.xvelocity = 0

        if self.right_pressed:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "right" and self.bbox_right == warp.x and
                        abs(self.y - warp.y) < WARP_LAX):
                    self.image_speed = WARP_SPEED * PLAYER_WALK_FRAMES_PER_PIXEL
                    warp.warp(self)

    def event_physics_collision_top(self, other, move_loss):
        xv = self.xvelocity
        for i in six.moves.range(CEILING_LAX):
            self.x -= 1
            if not self.get_top_touching_wall():
                self.move_y(-move_loss)
                break
        else:
            self.x += CEILING_LAX
            for i in six.moves.range(CEILING_LAX):
                self.x += 1
                if not self.get_top_touching_wall():
                    self.move_y(-move_loss)
                    break
            else:
                self.x -= CEILING_LAX
                self.yvelocity = 0

        for block in self.get_top_touching_wall():
            if isinstance(block, HittableBlock):
                block.hit(self)
            elif isinstance(block, HurtBottom):
                self.hurt()

        if self.up_pressed:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "up" and self.bbox_top == warp.y and
                        abs(self.x - warp.x) < WARP_LAX):
                    self.image_speed = WARP_SPEED * PLAYER_WALK_FRAMES_PER_PIXEL
                    warp.warp(self)
                    break

    def event_physics_collision_bottom(self, other, move_loss):
        for block in self.get_bottom_touching_wall():
            if isinstance(block, HurtTop):
                self.hurt()

        if isinstance(other, xsge_physics.SolidTop):
            self.yvelocity = 0
        elif isinstance(other, (xsge_physics.SlopeTopLeft,
                                xsge_physics.SlopeTopRight)):
            self.yvelocity = PLAYER_SLIDE_SPEED * (other.bbox_height /
                                                   other.bbox_width)

        if self.down_pressed:
            for warp in sge.game.current_room.warps:
                if (warp.direction == "down" and self.bbox_bottom == warp.y and
                        abs(self.x - warp.x) < WARP_LAX):
                    self.image_speed = WARP_SPEED * PLAYER_WALK_FRAMES_PER_PIXEL
                    warp.warp(self)


class DeadMan(sge.Object):

    """Object which falls off the screen, then gets destroyed."""

    gravity = PLAYER_GRAVITY
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

    gravity = ENEMY_GRAVITY
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


class InteractiveObject(sge.Object):

    active_range = ENEMY_ACTIVE_RANGE
    stompable = False
    knockable = False
    burnable = False
    freezable = False
    parent = None

    def update_active(self):
        for view in sge.game.current_room.views:
            if (self.bbox_left <= view.x + view.width + self.active_range and
                    self.bbox_right >= view.x - self.active_range and
                    self.bbox_top <= (view.y + view.height +
                                      self.active_range) and
                    self.bbox_bottom >= view.y - self.active_range):
                self.tangible = True
                self.active = True
                break
        else:
            self.tangible = False
            self.active = False

        if self.bbox_top > sge.game.current_room.height + self.active_range:
            self.destroy()

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

    def kick(self):
        self.drop()

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None

    def kick_up(self):
        self.kick()

    def touch_death(self):
        fall_sound.play()
        DeadMan.create(self.x, self.y, self.z, sprite=self.sprite,
                       xvelocity=self.xvelocity, yvelocity=0,
                       image_xscale=self.image_xscale,
                       image_yscale=-abs(self.image_yscale))
        self.destroy()

    def event_create(self):
        self.update_active()

    def event_begin_step(self, time_passed, delta_mult):
        self.move()

    def event_step(self, time_passed, delta_mult):
        self.update_active()

    def event_inactive_step(self, time_passed, delta_mult):
        self.update_active()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, Death):
            self.touch_death()

    def event_destroy(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None


class InteractiveCollider(InteractiveObject, xsge_physics.Collider):

    def stop_left(self):
        self.xvelocity = 0

    def stop_right(self):
        self.xvelocity = 0

    def stop_up(self):
        self.yvelocity = 0

    def stop_down(self):
        self.yvelocity = 0

    def touch_hurt(self):
        fall_sound.play()
        DeadMan.create(self.x, self.y, self.z, sprite=self.sprite,
                       xvelocity=self.xvelocity, yvelocity=0,
                       image_xscale=self.image_xscale,
                       image_yscale=-abs(self.image_yscale))
        self.destroy()

    def event_physics_collision_left(self, other, move_loss):
        if isinstance(other, HurtRight):
            self.touch_hurt()
        if isinstance(other, xsge_physics.SolidRight):
            self.stop_left()

    def event_physics_collision_right(self, other, move_loss):
        if isinstance(other, HurtLeft):
            self.touch_hurt()
        if isinstance(other, xsge_physics.SolidLeft):
            self.stop_right()

    def event_physics_collision_top(self, other, move_loss):
        if isinstance(other, HurtBottom):
            self.touch_hurt()
        if isinstance(other, xsge_physics.SolidBottom):
            self.stop_up()

    def event_physics_collision_bottom(self, other, move_loss):
        if isinstance(other, HurtTop):
            self.touch_hurt()
        if isinstance(other, xsge_physics.SolidTop):
            self.stop_down()


class FallingObject(InteractiveCollider):

    """
    Falls based on gravity. If on a slope, falls at a constant speed
    based on the steepness of the slope.
    """

    gravity = ENEMY_GRAVITY
    fall_speed = ENEMY_FALL_SPEED
    slide_speed = ENEMY_SLIDE_SPEED
    was_on_floor = False

    def move(self):
        on_floor = self.get_bottom_touching_wall()
        on_slope = self.get_bottom_touching_slope()
        if self.was_on_floor and (on_floor or on_slope) and self.yvelocity >= 0:
            self.yacceleration = 0
            if on_floor:
                self.yvelocity = 0
            else:
                assert on_slope
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

    def set_direction(self, direction):
        self.xvelocity = self.walk_speed * direction
        self.image_xscale = abs(self.image_xscale) * direction

    def move(self):
        super(WalkingObject, self).move()

        if not self.xvelocity:
            player = None
            dist = 0
            for obj in sge.game.current_room.objects:
                if isinstance(obj, Player):
                    ndist = math.hypot(self.x - obj.x, self.y - obj.y)
                    if player is None or ndist < dist:
                        player = obj
                        dist = ndist

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

    def event_inactive_step(self, time_passed, delta_mult):
        self.xvelocity = 0
        self.update_active()


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

    def knock(self, other=None):
        fall_sound.play()
        DeadMan.create(self.x, self.y, self.z, sprite=self.sprite,
                       xvelocity=self.xvelocity,
                       yvelocity=-ENEMY_HIT_BELOW_SPEED,
                       image_xscale=self.image_xscale,
                       image_yscale=-abs(self.image_yscale))
        self.destroy()


class FreezableObject(InteractiveObject):

    """Provides basic freeze behavior."""

    frozen_sprite = None

    def freeze(self):
        # TODO: Create ice block with frozen_sprite if possible, or the
        # current sprite of the object otherwise.
        self.destroy()


class BurnableObject(InteractiveObject):

    """Provides basic burn behavior."""

    def burn(self):
        fall_sound.play()
        DeadMan.create(self.x, self.y, self.z, sprite=self.sprite,
                       xvelocity=self.xvelocity, yvelocity=0,
                       image_xscale=self.image_xscale,
                       image_yscale=-abs(self.image_yscale))
        self.destroy()


class WalkingSnowball(CrowdObject, KnockableObject, BurnableObject):

    def event_create(self):
        self.sprite = snowball_walk_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None
        self.x += self.image_origin_x
        self.y += self.image_origin_y

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.stomp_jump(self)
        squish_sound.play()
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


class WalkingIceblock(CrowdObject, KnockableObject, BurnableObject):

    stayonplatform = True

    def event_create(self):
        self.sprite = iceblock_walk_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None
        self.x += self.image_origin_x
        self.y += self.image_origin_y

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.stomp_jump(self)
        stomp_sound.play()
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)
        FlatIceblock.create(self.x, self.y, self.z, sprite=iceblock_flat_sprite,
                            image_xscale=self.image_xscale,
                            image_yscale=self.image_yscale)
        self.destroy()

    def knock(self, other=None):
        super(WalkingIceblock, self).knock(other)
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)

    def burn(self):
        super(WalkingIceblock, self).burn()
        sge.game.current_room.add_points(ENEMY_KILL_POINTS)


class FlatIceblock(CrowdBlockingObject, FallingObject, KnockableObject,
                   BurnableObject):

    def touch(self, other):
        if other.pickup(self):
            self.parent = other
            self.gravity = 0
            if other.action_pressed:
                other.action()

    def knock(self, other=None):
        if self.parent is not None and other is not None:
            other.knock(self)
        super(FlatIceblock, self).knock(other)

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None
            self.gravity = self.__class__.gravity

    def kick(self):
        if self.parent is not None:
            self.parent.kick_object()
            kick_sound.play()
            dib = DashingIceblock.create(self.parent, self.x, self.y, self.z,
                                         sprite=self.sprite,
                                         image_xscale=self.image_xscale,
                                         image_yscale=self.image_yscale)
            dib.set_direction(-1 if self.parent.image_xscale < 0 else 1)
            self.parent = None
            self.destroy()

    def kick_up(self):
        if self.parent is not None:
            self.parent.kick_object()
            kick_sound.play()
            tib = ThrownIceblock.create(self.parent, self.x, self.y, self.z,
                                        sprite=self.sprite,
                                        image_xscale=self.image_xscale,
                                        image_yscale=self.image_yscale,
                                        xvelocity=self.parent.xvelocity,
                                        yvelocity=-KICK_UP_SPEED)
            self.parent = None
            self.destroy()

    def event_end_step(self, time_passed, delta_mult):
        if self.parent is not None:
            direction = -1 if self.parent.image_xscale < 0 else 1
            self.image_xscale = abs(self.image_xscale) * direction


class ThrownIceblock(FallingObject, KnockableObject, BurnableObject):

    fall_speed = ICEBLOCK_FALL_SPEED

    def __init__(self, thrower, *args, **kwargs):
        self.thrower = thrower
        super(ThrownIceblock, self).__init__(*args, **kwargs)

    def touch(self, other):
        fib = FlatIceblock.create(self.x, self.y, self.z, sprite=self.sprite,
                                  image_xscale=self.image_xscale,
                                  image_yscale=self.image_yscale)
        self.destroy()
        fib.touch(other)

    def stop_left(self):
        iceblock_bump_sound.play()
        self.xvelocity = abs(self.xvelocity)
        self.set_direction(1)
        for block in self.get_left_touching_wall():
            if isinstance(block, HittableBlock):
                block.hit(self.thrower)

    def stop_right(self):
        iceblock_bump_sound.play()
        self.xvelocity = -abs(self.xvelocity)
        self.set_direction(-1)
        for block in self.get_right_touching_wall():
            if isinstance(block, HittableBlock):
                block.hit(self.thrower)

    def stop_up(self):
        self.yvelocity = 0
        for block in self.get_top_touching_wall():
            if isinstance(block, HittableBlock):
                block.hit(self.thrower)

    def event_end_step(self, time_passed, delta_mult):
        if (self.yvelocity >= 0 and
                (self.get_bottom_touching_wall() or
                 self.get_bottom_touching_slope())):
            self.xdeceleration = ICEBLOCK_FRICTION
            if abs(self.xvelocity) <= 0.05:
                FlatIceblock.create(self.x, self.y, self.z, sprite=self.sprite,
                                    image_xscale=self.image_xscale,
                                    image_yscale=self.image_yscale)
                self.destroy()
        else:
            self.xdeceleration = 0

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, InteractiveObject):
            other.knock(self)
        elif isinstance(other, Coin):
            other.event_collision(self.thrower, -xdirection, -ydirection)

        super(ThrownIceblock, self).event_collision(other, xdirection,
                                                    ydirection)


class DashingIceblock(WalkingObject, KnockableObject, BurnableObject):

    walk_speed = ICEBLOCK_DASH_SPEED

    def __init__(self, thrower, *args, **kwargs):
        self.thrower = thrower
        super(DashingIceblock, self).__init__(*args, **kwargs)

    def stop_left(self):
        iceblock_bump_sound.play()
        self.set_direction(1)
        for block in self.get_left_touching_wall():
            if isinstance(block, HittableBlock):
                block.hit(self.thrower)

    def stop_right(self):
        iceblock_bump_sound.play()
        self.set_direction(-1)
        for block in self.get_right_touching_wall():
            if isinstance(block, HittableBlock):
                block.hit(self.thrower)

    def touch(self, other):
        other.hurt()

    def stomp(self, other):
        other.stomp_jump(self)
        stomp_sound.play()
        FlatIceblock.create(self.x, self.y, self.z, sprite=iceblock_flat_sprite,
                            image_xscale=self.image_xscale,
                            image_yscale=self.image_yscale)
        self.destroy()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, InteractiveObject):
            other.knock(self)
        elif isinstance(other, Coin):
            other.event_collision(self.thrower, -xdirection, -ydirection)

        super(DashingIceblock, self).event_collision(other, xdirection,
                                                     ydirection)

    def event_inactive_step(self, time_passed, delta_mult):
        self.destroy()


class FireFlower(FallingObject):

    def event_create(self):
        self.sprite = fire_flower_sprite
        self.image_fps = None
        self.image_origin_x = None
        self.image_origin_y = None
        self.bbox_x = None
        self.bbox_y = None
        self.bbox_width = None
        self.bbox_height = None
        self.x += self.image_origin_x
        self.y += self.image_origin_y

        self.ammo = 15

    def touch(self, other):
        if other.pickup(self):
            self.parent = other
            self.gravity = 0

    def knock(self, other=None):
        self.yvelocity = -ENEMY_HIT_BELOW_SPEED

    def drop(self):
        if self.parent is not None:
            self.parent.drop_object()
            self.parent = None
            self.gravity = self.__class__.gravity

    def kick(self):
        if self.parent is not None:
            if self.ammo > 0:
                # TODO: Create bullet
                self.ammo -= 1
                shoot_sound.play()
            else:
                # TODO: Throw flower
                pass


class HittableBlock(xsge_physics.SolidBottom, Tile):

    hit_sprite = None

    def event_create(self):
        self.hit_obj = None

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
        brick_sound.play()
        if self.hit_obj is not None:
            self.hit_obj.destroy()
            self.hit_obj = None

        if isinstance(self, xsge_physics.SolidTop):
            for obj in self.collision(InteractiveObject, y=(self.y - 1)):
                obj.knock()

        if self.hit_sprite is not None:
            s = self.hit_sprite
        else:
            s = self.sprite

        self.visible = False
        self.hit_obj = sge.Object.create(
            self.x, self.y, self.z, sprite=s, tangible=False,
            yvelocity=(-BLOCK_HIT_SPEED), yacceleration=BLOCK_HIT_GRAVITY,
            image_index=self.image_index,
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

    def event_create(self):
        super(Brick, self).event_create()
        self.sprite = brick_sprite

    def event_hit(self, other):
        # TODO: Create brick shards (probably DeadMan objects)
        sge.game.current_room.add_points(10)
        self.destroy()


class CoinBrick(Brick):

    def event_create(self):
        super(CoinBrick, self).event_create()
        self.coins = COINBRICK_COINS

    def event_alarm(self, alarm_id):
        if alarm_id == "decay":
            self.coins -= 1
            self.alarms["decay"] = COINBRICK_DECAY_TIME

    def event_hit(self, other):
        if self.coins > 0:
            self.coins -= 1
            CoinCollect.create(self.x, self.y, z=(self.z + 0.5))
            other.coins += 1

            if "decay" not in self.alarms:
                self.alarms["decay"] = COINBRICK_DECAY_TIME
        else:
            super(CoinBrick, self).event_hit(other)


class EmptyBlock(HittableBlock, xsge_physics.Solid):

    pass


class HiddenItemBlock(HittableBlock):

    def __init__(self, x, y, item=None, **kwargs):
        super(HiddenItemBlock, self).__init__(x, y, **kwargs)
        self.item = item

    def event_create(self):
        super(HiddenItemBlock, self).event_create()
        self.sprite = None
        self.hit_sprite = bonus_empty_sprite

    def event_hit(self, other):
        if self.item and self.item in TYPES:
            obj = TYPES[self.item].create(self.x, self.y, z=(self.z - 0.5))
            obj.bbox_left = self.bbox_left
            obj.x = (self.x - self.image_origin_x + self.sprite.width / 2 +
                     obj.image_origin_x - obj.sprite.width / 2)
            obj.bbox_bottom = self.bbox_top
            find_powerup_sound.play()
        else:
            CoinCollect.create(self.x, self.y, z=(self.z + 0.5))
            other.coins += 1

    def event_hit_end(self):
        EmptyBlock.create(self.x, self.y, z=self.z, sprite=bonus_empty_sprite)
        self.destroy()


class ItemBlock(HiddenItemBlock, xsge_physics.Solid):

    def event_create(self):
        super(ItemBlock, self).event_create()
        self.sprite = bonus_full_sprite
        self.image_fps = None


class InfoBlock(HittableBlock, xsge_physics.Solid):

    def __init__(self, x, y, text="(null)", **kwargs):
        super(InfoBlock, self).__init__(x, y, **kwargs)
        self.text = text


class Lava(xsge_tmx.Decoration):

    def event_create(self):
        self.sprite = lava_body_sprite
        self.image_fps = None
        self.active = True


class LavaSurface(xsge_tmx.Decoration):

    def event_create(self):
        self.sprite = lava_surface_sprite
        self.image_fps = None
        self.active = True


class Goal(xsge_tmx.Decoration):

    def event_create(self):
        self.sprite = goal_sprite
        self.image_fps = None
        self.active = True


class GoalTop(xsge_tmx.Decoration):

    def event_create(self):
        self.sprite = goal_top_sprite
        self.image_fps = None
        self.active = True


class Coin(Tile):

    def __init__(self, x, y, **kwargs):
        super(Coin, self).__init__(x, y, **kwargs)
        self.sprite = coin_sprite
        self.image_fps = None
        self.checks_collisions = False
        self.active = False

    def event_inactive_step(self, time_passed, delta_mult):
        self.image_index = coin_animation.image_index
        Tile.event_step(self, time_passed, delta_mult)

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, Player) and self in sge.game.current_room.objects:
            CoinCollect.create(self.x, self.y, z=self.z,
                               image_index=self.image_index)
            self.destroy()
            other.coins += 1


class CoinCollect(sge.Object):

    def __init__(self, x, y, **kwargs):
        super(CoinCollect, self).__init__(x, y, **kwargs)
        self.sprite = coin_sprite
        self.image_fps = coin_sprite.fps
        self.tangible = False

    def event_create(self):
        coin_sound.play()
        sge.game.current_room.add_points(COIN_POINTS)
        self.alarms["destroy"] = COIN_COLLECT_TIME
        self.yvelocity = -COIN_COLLECT_SPEED

    def event_step(self, time_passed, delta_mult):
        T = self.alarms.get("destroy", COIN_COLLECT_TIME)
        self.image_alpha = 255 * (T / COIN_COLLECT_TIME)

    def event_alarm(self, alarm_id):
        if alarm_id == "destroy":
            self.destroy()


class WarpSpawn(xsge_path.Path):

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
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)
            elif self.end_direction == "right":
                if obj.bbox_left >= x:
                    obj.bbox_left = x
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(0, 0, math.floor(x - left_edge),
                                           warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)
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
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)
            elif self.end_direction == "down":
                if obj.bbox_top >= y:
                    obj.bbox_top = y
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(0, 0, warp_sprite.width,
                                           math.floor(y - top_edge))
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)

        for obj in finished:
            obj.visible = True
            obj.tangible = True
            obj.warping = False
            obj.speed = 0
            self.warps_out.remove(obj)

    def event_follow_end(self, obj):
        if self.dest and ":" in self.dest:
            cr = sge.game.current_room
            level_f, spawn = self.dest.split(":", 1)
            level = Level.load(level_f)
            level.spawn = spawn
            level.points = cr.points
            level.time_bonus = cr.time_bonus

            for nobj in level.objects:
                if isinstance(nobj, Player):
                    for cobj in cr.objects:
                        if (isinstance(cobj, Player) and
                                cobj.player == nobj.player):
                            nobj.hp = cobj.hp
                            nobj.coins = cobj.coins

                            if cobj.held_object is not None:
                                nobj.held_object = cobj.held_object
                                cr.remove(cobj.held_object)
                                nobj.held_object.parent = nobj
                                level.add(nobj.held_object)

                            break

            level.start()
        else:
            pipe_sound.play()
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
                obj.move_direction = 90
            elif self.end_direction == "down":
                obj.x = x
                obj.y = y + obj.sprite.origin_y - obj.sprite.height
                obj.move_direction = 270

            obj.speed = WARP_SPEED
            obj.xacceleration = 0
            obj.yacceleration = 0
            obj.xdeceleration = 0
            obj.ydeceleration = 0


class Warp(WarpSpawn):

    def __init__(self, x, y, points=(), dest=None, **kwargs):
        super(Warp, self).__init__(x, y, points=points, dest=dest, **kwargs)
        self.warps_in = []

    def warp(self, other):
        pipe_sound.play()
        self.warps_in.append(other)
        other.visible = False
        other.tangible = False
        other.warping = True
        other.move_direction = {"right": 0, "up": 90, "left": 180,
                                "down": 270}.get(self.direction, 0)
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
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)
            elif self.direction == "right":
                if obj.x >= self.x + obj.image_origin_x:
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(
                        math.ceil(self.x - left_edge), 0, warp_sprite.width,
                        warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)
            elif self.direction == "up":
                if obj.y <= self.y + obj.image_origin_y - obj.sprite.height:
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(0, 0, warp_sprite.width,
                                           math.floor(self.y - top_edge))
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)
            elif self.direction == "down":
                if obj.y >= self.y + obj.image_origin_y:
                    finished.append(obj)
                else:
                    warp_sprite = get_scaled_copy(obj)
                    warp_sprite.draw_erase(
                        0, math.ceil(self.y - top_edge), warp_sprite.width,
                        warp_sprite.height)
                    sge.game.current_room.project_sprite(
                        warp_sprite, obj.image_index, obj.x, obj.y, obj.z)

        for obj in finished:
            obj.x = self.x
            obj.y = self.y
            self.follow_start(obj, WARP_SPEED)
            self.warps_in.remove(obj)

    def event_destroy(self):
        while self in sge.game.current_room.warps:
            sge.game.current_room.warps.remove(self)


def get_object(x, y, cls=None, **kwargs):
    cls = TYPES.get(cls, sge.Object)
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
    return s


def play_music(music, force_restart=False):
    """Play the given music file, starting with its start piece."""
    if music:
        music_object = loaded_music.get(music)
        if music_object is None:
            try:
                music_object = sge.Music(os.path.join(DATA, "music", music))
            except IOError:
                sge.Music.clear_queue()
                sge.Music.stop()
                return
            else:
                loaded_music[music] = music_object

        name, ext = os.path.splitext(music)
        music_start = ''.join((name, "-start", ext))
        music_start_object = loaded_music.get(music_start)
        if music_start_object is None:
            try:
                music_start_object = sge.Music(os.path.join(DATA, "music",
                                                            music_start))
            except IOError:
                music_start_object = music_object
            else:
                loaded_music[music_start] = music_start_object

        if (force_restart or
                (not music_object.playing and not music_start_object.playing)):
            sge.Music.clear_queue()
            sge.Music.stop()
            music_start_object.play()
            music_object.queue(loops=None)
    else:
        sge.Music.clear_queue()
        sge.Music.stop()


TYPES = {"solid_left": SolidLeft, "solid_right": SolidRight,
         "solid_top": SolidTop, "solid_bottom": SolidBottom, "solid": Solid,
         "slope_topleft": SlopeTopLeft, "slope_topright": SlopeTopRight,
         "slope_bottomleft": SlopeBottomLeft,
         "slope_bottomright": SlopeBottomRight, "spike_left": SpikeLeft,
         "spike_right": SpikeRight, "spike_top": SpikeTop,
         "spike_bottom": SpikeBottom, "death": Death, "level_end": LevelEnd,
         "creatures": get_object, "hazards": get_object,
         "special_blocks": get_object, "decoration_small": get_object,
         "player": Player, "walking_snowball": WalkingSnowball,
         "walking_iceblock": WalkingIceblock, "fireflower": FireFlower,
         "brick": Brick,
         "coinbrick": CoinBrick, "emptyblock": EmptyBlock,
         "itemblock": ItemBlock, "hiddenblock": HiddenItemBlock,
         "infoblock": InfoBlock, "lava": Lava, "lava_surface": LavaSurface,
         "goal": Goal, "goal_top": GoalTop, "coin": Coin, "warp": Warp,
         "warp_spawn": WarpSpawn}


Game(SCREEN_SIZE[0], SCREEN_SIZE[1], scale_smooth=False, fps=FPS, delta=True,
     delta_min=15, window_text="reTux {}".format(__version__),
     window_icon=os.path.join(DATA, "images", "misc", "icon.png"))
xsge_gui.init()

# Load sprites
d = os.path.join(DATA, "images", "objects", "tux")
tux_body_stand_sprite = sge.Sprite(
    "tux_body_stand", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_stand_sprite = sge.Sprite(
    "tux_arms_stand", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_idle_sprite = sge.Sprite(
    "tux_body_idle", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_idle_sprite = sge.Sprite(
    "tux_arms_stand", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_walk_sprite = sge.Sprite(
    "tux_body_walk", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_walk_sprite = sge.Sprite(
    "tux_arms_walk", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
# TODO: Proper separate run sprite
tux_body_run_sprite = sge.Sprite(
    "tux_body_walk", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_run_sprite = sge.Sprite(
    "tux_arms_kick", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_skid_sprite = sge.Sprite(
    "tux_body_skid", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_skid_sprite = sge.Sprite(
    "tux_arms_skid", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_jump_sprite = sge.Sprite(
    "tux_body_jump", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_jump_sprite = sge.Sprite(
    "tux_arms_jump", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_fall_sprite = tux_body_jump_sprite.copy()
tux_arms_fall_sprite = sge.Sprite(
    "tux_arms_fall", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_body_kick_sprite = sge.Sprite(
    "tux_body_kick", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_kick_sprite = sge.Sprite(
    "tux_arms_kick", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_grab_sprite = sge.Sprite(
    "tux_arms_grab", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_arms_skid_grab_sprite = sge.Sprite(
    "tux_arms_skid_grab", d, origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
tux_die_sprite = sge.Sprite("tux_die", d, origin_x=32, origin_y=11, fps=8)

tux_body_walk_reverse_sprite = sge.Sprite(
    width=tux_body_walk_sprite.width, height=tux_body_walk_sprite.height,
    origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
i = 0
while True:
    tux_body_walk_reverse_sprite.draw_sprite(
        tux_body_walk_sprite, i, tux_body_walk_sprite.origin_x,
        tux_body_walk_sprite.origin_y, frame=0)
    i += 1
    if i >= tux_body_walk_sprite.frames:
        break
    tux_body_walk_reverse_sprite.insert_frame(0)

tux_arms_walk_reverse_sprite = sge.Sprite(
    width=tux_arms_walk_sprite.width, height=tux_arms_walk_sprite.height,
    origin_x=TUX_ORIGIN_X, origin_y=TUX_ORIGIN_Y)
i = 0
while True:
    tux_arms_walk_reverse_sprite.draw_sprite(
        tux_arms_walk_sprite, i, tux_arms_walk_sprite.origin_x,
        tux_arms_walk_sprite.origin_y, frame=0)
    i += 1
    if i >= tux_arms_walk_sprite.frames:
        break
    tux_arms_walk_reverse_sprite.insert_frame(0)

tux_stand_sprite = tux_body_stand_sprite.copy()
tux_idle_sprite = tux_body_idle_sprite.copy()
tux_walk_sprite = tux_body_walk_sprite.copy()
tux_walk_reverse_sprite = tux_body_walk_reverse_sprite.copy()
tux_run_sprite = tux_body_run_sprite.copy()
tux_skid_sprite = tux_body_skid_sprite.copy()
tux_jump_sprite = tux_body_jump_sprite.copy()
tux_fall_sprite = tux_body_fall_sprite.copy()
tux_kick_sprite = tux_body_kick_sprite.copy()

for bs, a in [(tux_stand_sprite, tux_arms_stand_sprite),
              (tux_idle_sprite, tux_arms_idle_sprite),
              (tux_walk_sprite, tux_arms_walk_sprite),
              (tux_walk_reverse_sprite, tux_arms_walk_reverse_sprite),
              (tux_run_sprite, tux_arms_run_sprite),
              (tux_skid_sprite, tux_arms_skid_sprite),
              (tux_jump_sprite, tux_arms_jump_sprite),
              (tux_fall_sprite, tux_arms_fall_sprite),
              (tux_kick_sprite, tux_arms_kick_sprite)]:
    for i in six.moves.range(bs.frames):
        bs.draw_sprite(a, i, bs.origin_x, bs.origin_y, i)

d = os.path.join(DATA, "images", "objects", "enemies")
snowball_walk_sprite = sge.Sprite("snowball", d, origin_x=19, origin_y=4,
                                  fps=8, bbox_x=-13, bbox_y=0,
                                  bbox_width=26, bbox_height=32)
snowball_squished_sprite = sge.Sprite("snowball_squished", d, origin_x=17,
                                      origin_y=-19, bbox_x=-13, bbox_y=19,
                                      bbox_width=26, bbox_height=13)
iceblock_walk_sprite = sge.Sprite("iceblock", d, origin_x=18, origin_y=6,
                                  fps=10, bbox_x=-13, bbox_y=1, bbox_width=25,
                                  bbox_height=31)
iceblock_flat_sprite = sge.Sprite("iceblock_flat", d, origin_x=18, origin_y=6,
                                  bbox_x=-16, bbox_y=1, bbox_width=31,
                                  bbox_height=28)

d = os.path.join(DATA, "images", "objects", "bonus")
bonus_empty_sprite = sge.Sprite("bonus_empty", d)
bonus_full_sprite = sge.Sprite("bonus_full", d, fps=8)
brick_sprite = sge.Sprite("brick", d)
coin_sprite = sge.Sprite("coin", d, fps=8)
fire_flower_sprite = sge.Sprite("fire_flower", d, origin_x=0, origin_y=8,
                                fps=8, bbox_x=8, bbox_y=0, bbox_width=16,
                                bbox_height=24)

d = os.path.join(DATA, "images", "objects", "decoration")
lava_body_sprite = sge.Sprite("lava_body", d, transparent=False, fps=5)
lava_surface_sprite = sge.Sprite("lava_surface", d, fps=5)
goal_sprite = sge.Sprite("goal", d, fps=8)
goal_top_sprite = sge.Sprite("goal_top", d, fps=8)

d = os.path.join(DATA, "images", "misc")
heart_empty_sprite = sge.Sprite("heart_empty", d, origin_y=-1)
heart_half_sprite = sge.Sprite("heart_half", d, origin_y=-1)
heart_full_sprite = sge.Sprite("heart_full", d, origin_y=-1)

coin_icon_sprite = coin_sprite.copy()
coin_icon_sprite.width = 16
coin_icon_sprite.height = 16
coin_icon_sprite.origin_y = -1

# Load backgrounds
d = os.path.join(DATA, "images", "backgrounds")

layers = [
    sge.BackgroundLayer(
        sge.Sprite("arctis1-middle", d), 0, 0, -100000, xscroll_rate=0.5,
        yscroll_rate=0.5, repeat_left=True, repeat_right=True),
    sge.BackgroundLayer(
        sge.Sprite("arctis1-bottom", d), 0, 352, -100000, xscroll_rate=0.5,
        yscroll_rate=0.5, repeat_left=True, repeat_right=True,
        repeat_down=True),
    sge.BackgroundLayer(
        sge.Sprite("arctis2-middle", d), 0, 0, -100010, xscroll_rate=0.25,
        yscroll_rate=0.25, repeat_left=True, repeat_right=True),
    sge.BackgroundLayer(
        sge.Sprite("arctis2-bottom", d), 0, 352, -100010, xscroll_rate=0.25,
        yscroll_rate=0.25, repeat_left=True, repeat_right=True,
        repeat_down=True),
    sge.BackgroundLayer(
        sge.Sprite("arctis3", d), 0, 0, -100020, xscroll_rate=0,
        yscroll_rate=0.25, repeat_left=True, repeat_right=True)]
backgrounds["arctis"] = sge.Background(layers, sge.Color((109, 92, 230)))

cave_edge_spr = sge.Sprite("cave-edge", d)
layers = [
    sge.BackgroundLayer(
        sge.Sprite("cave-middle", d), 0, 128, -100000, xscroll_rate=0.9,
        yscroll_rate=0.9, repeat_left=True, repeat_right=True),
    sge.BackgroundLayer(
        cave_edge_spr, 0, 0, -100000, xscroll_rate=0.9, yscroll_rate=0.9,
        repeat_left=True, repeat_right=True, repeat_up=True),
    sge.BackgroundLayer(
        cave_edge_spr, 0, 256, -100000, xscroll_rate=0.9, yscroll_rate=0.9,
        repeat_left=True, repeat_right=True, repeat_down=True)]
del cave_edge_spr
backgrounds["cave"] = sge.Background(layers, sge.Color("black"))

for i in list(backgrounds.keys()):
    layers = backgrounds[i].layers + [
        sge.BackgroundLayer(sge.Sprite("castle", d), 0, -64, -99000,
                            repeat_left=True, repeat_right=True,
                            repeat_up=True),
        sge.BackgroundLayer(sge.Sprite("castle-bottom", d), 0, 536, -99000,
                            repeat_left=True, repeat_right=True,
                            repeat_down=True)]

    backgrounds["{}_castle".format(i)] = sge.Background(layers,
                                                        backgrounds[i].color)

# Load fonts
font_sprite = sge.Sprite.from_tileset(
    os.path.join(DATA, "images", "misc", "font.png"), columns=16, rows=20,
    width=16, height=18)

chars = (['\x00'] + [six.unichr(i) for i in six.moves.range(33, 128)] +
         [six.unichr(i) for i in six.moves.range(160, 384)])
font = sge.Font.from_sprite(font_sprite, chars, size=18)

# Load sounds
jump_sound = sge.Sound(os.path.join(DATA, "sounds", "jump.wav"))
skid_sound = sge.Sound(os.path.join(DATA, "sounds", "skid.wav"), 50)
hurt_sound = sge.Sound(os.path.join(DATA, "sounds", "hurt.wav"))
kill_sound = sge.Sound(os.path.join(DATA, "sounds", "kill.wav"))
brick_sound = sge.Sound(os.path.join(DATA, "sounds", "brick.wav"))
coin_sound = sge.Sound(os.path.join(DATA, "sounds", "coin.wav"))
find_powerup_sound = sge.Sound(os.path.join(DATA, "sounds", "upgrade.wav"))
heal_sound = sge.Sound(os.path.join(DATA, "sounds", "heal.wav"))
shoot_sound = sge.Sound(os.path.join(DATA, "sounds", "shoot.wav"))
squish_sound = sge.Sound(os.path.join(DATA, "sounds", "squish.wav"))
stomp_sound = sge.Sound(os.path.join(DATA, "sounds", "stomp.wav"))
kick_sound = sge.Sound(os.path.join(DATA, "sounds", "kick.wav"))
iceblock_bump_sound = sge.Sound(os.path.join(DATA, "sounds",
                                             "iceblock_bump.wav"))
fall_sound = sge.Sound(os.path.join(DATA, "sounds", "fall.wav"))
pipe_sound = sge.Sound(os.path.join(DATA, "sounds", "pipe.ogg"))

# Load music
invincible_music = sge.Music(os.path.join(DATA, "music", "invincible.ogg"))
level_win_music = sge.Music(os.path.join(DATA, "music", "leveldone.ogg"))
no_music = sge.Music(None)
loaded_music["invincible.ogg"] = invincible_music
loaded_music["leveldone.ogg"] = level_win_music
loaded_music[None] = no_music

# Create objects
coin_animation = sge.Object(0, 0, sprite=coin_sprite, visible=False,
                            tangible=False)
bonus_animation = sge.Object(0, 0, sprite=bonus_empty_sprite, visible=False,
                             tangible=False)

# Create rooms
sge.game.start_room = Level.load("1-01.tmx")

sge.game.mouse.visible = False


if __name__ == '__main__':
    sge.game.start()
