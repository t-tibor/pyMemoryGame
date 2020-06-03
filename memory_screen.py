import random
import os
import functools

from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics import Rectangle, Color
from kivy.properties import NumericProperty
from kivy.animation import Animation
from kivy.clock import Clock
from highscore_screen import HighScorePopup, HighScoreViewer
from utils import *
from highscore_database import DB
import itertools
from math import ceil
v = 0


class SimpleCard(Widget):

    cover_ratio = NumericProperty(1)

    def __init__(self, table, key, picture_path, **kwargs):
        super(SimpleCard, self).__init__(**kwargs)

        self.table = table
        self.key = key
        self.picture_path = picture_path

        self.is_in_game = True
        self.is_shown = False
        self.is_animation_running = False

        self.animation_type = kwargs.get('animation_type', 'out_elastic')

        # plotting
        with self.canvas:
            Color(1, 1, 1, 1)
            self. picture = Rectangle(source=self.picture_path, pos=self.pos, size=self.size)
            Color(0, 1, 0, 1)
            self.cover = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_canvas, size=self.update_canvas)

        self.bind(cover_ratio=self.update_cover)

    def update_cover(self, *args):
        self.cover.pos = self.pos
        self.cover.size = (self.size[0] * self.cover_ratio, self.size[1])

    def update_canvas(self, *args):
        global v
        print('canvas update %d' % v)
        v += 1
        self.picture.pos = self.pos
        self.picture.size = self.size
        self.update_cover()

    def _clicked(self):
        self.table.on_card_click(self)

    def _animation_ready(self, *args):
        self.is_animation_running = False
        self.table.on_animation_ready(self)

    def is_animation_ready(self):
        return not self.is_animation_running

    def show(self):
        self.is_shown = True
        self.is_animation_running = True
        anim = Animation(cover_ratio=0.05, duration=0.5, t=self.animation_type)
        anim.bind(on_complete=self._animation_ready)
        anim.start(self)

    def hide(self):
        self.is_shown = False
        self.is_animation_running = True
        anim = Animation(cover_ratio=1, duration=0.5, t=self.animation_type)
        anim.bind(on_complete=self._animation_ready)
        anim.start(self)

    def remove(self):
        self.is_in_game = False
        self.cover_ratio = 0

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.is_in_game:
                print('Click on card with id:' + str(self.key))
                self._clicked()
            return True
        return False

    def reset(self):
        self.is_in_game = True
        Animation.cancel_all(self)
        self.cover_ratio = 1


def matrix_pos_generator(size_x, size_y):
    for x in range(size_x):
        for y in range(size_y):
            yield (x, y)


def load_pictures(path='./pictures'):
    if not os.path.isdir(path):
        raise Exception('Given folder: %s does not exists' % path)
    file_list = [os.path.join(path, fname) for fname in os.listdir(path) if fname.endswith('.png') or fname.endswith('.jpg')]
    random.shuffle(file_list)
    return file_list


class MemoryTable(FloatLayout):
    score = NumericProperty()
    click_cnt = NumericProperty()

    cards_x = NumericProperty(5)
    cards_y = NumericProperty(4)
    card_aspect_ratio = NumericProperty(1.0)   # x / y

    def __init__(self, **kwargs):
        super(FloatLayout, self).__init__(**kwargs)

        self.picture_paths = load_pictures()
        self.picture_ids = range(0, len(self.picture_paths))
        self.pictures = [{'path': p, 'id': id} for p,id in zip(self.picture_paths, self.picture_ids)]

        self.cardCount = 0
        self.selected1 = None
        self.selected2 = None
        self.cardsLeft = self.cards_x * self.cards_y
        self.score = 0
        self.click_cnt = 0
        self.Cards = list()
        self.click_handler = self._state_empty
        self.animation_rdy_handler = None

        self.register_event_type('on_finish')
        self.register_event_type('on_pair_found')

    def picture_generator(self, cnt):
        picture_iterator = itertools.cycle(self.pictures)
        for _ in range(int(cnt/2)):
            pic = next(picture_iterator)
            yield pic
            yield pic

    def create_cards(self, cnt):
        return [SimpleCard(self, pic['id'], pic['path']) for pic in self.picture_generator(cnt)]

    def reset_game(self, *args):
        self.cardCount = self.cards_x * self.cards_y
        if self.cardCount % 2 == 1:
            raise Exception('Invalid card count')

        self.clear_widgets()
        self.Cards = self.create_cards(self.cardCount)
        random.shuffle(self.Cards)
        for card in self.Cards:
            self.add_widget(card)

        self.do_card_layout()

        self.score = 0
        self.click_cnt = 0
        self.click_handler = self._state_empty
        self.animation_rdy_handler = None
        self.cardsLeft = self.cards_x * self.cards_y

    def do_card_layout(self):
        space_ratio = 0.1
        full_h_ratio = self.cards_x + (self.cards_x - 1) * space_ratio
        full_v_ratio = self.cards_y + (self.cards_y - 1) * space_ratio
        bbox_x = self.width / full_h_ratio
        bbox_y = self.height / full_v_ratio
        bbox_ratio = bbox_x / bbox_y
        if self.card_aspect_ratio > bbox_ratio:
            s_x = bbox_x
            s_y = s_x / self.card_aspect_ratio
        else:
            s_y = bbox_y
            s_x = s_y * self.card_aspect_ratio

        x_pad = (bbox_x - s_x)/2.0
        y_pad = (bbox_y - s_y)/2.0

        for (card, coord) in zip(self.Cards, matrix_pos_generator(self.cards_x, self.cards_y)):
            pos_x = coord[0]
            pos_y = coord[1]

            # card.size_hint = (1.0 / full_h_ratio, 1.0 / full_w_ratio)
            card.size_hint = (None, None)
            card.size = (s_x, s_y)
            card.pos_hint = {'x': (1.0 + space_ratio) / full_h_ratio * pos_x + x_pad/self.width,
                             'y': (1.0 + space_ratio) / full_v_ratio * pos_y + y_pad/self.height}
            card.reset()

    def on_finish(*args, **kwargs):
        pass

    def on_pair_found(*args, **kwargs):
        pass

    def _state_empty(self,  card):
        self.click_handler = self._state_ongoing_selection
        self.animation_rdy_handler = None
        self.selected1 = card
        card.show()

    def _state_ongoing_selection(self, card):
        if card == self.selected1:
            self.click_handler = self._state_empty
            self.animation_rdy_handler = None
            card.hide()
            return

        self.click_handler = None
        self.animation_rdy_handler = self._state_wait_for_animation_ready
        self.selected2 = card
        card.show()

    def _state_wait_for_animation_ready(self, card):
        if self.selected1.is_animation_ready() and self.selected2.is_animation_ready():
            self.click_handler = self._state_empty
            self.animation_rdy_handler = None

            if self.selected1.key == self.selected2.key:
                self.selected1.remove()
                self.selected2.remove()
                self.cardsLeft = self.cardsLeft - 2
                self.score = self.score + 1

                print('Pair found')
                print('Cards left: %d' % self.cardsLeft)
                self.dispatch('on_pair_found')
                if self.cardsLeft <= 0:
                    print('Game ended')
                    self.dispatch('on_finish', self.score)
            else:
                self.selected1.hide()
                self.selected2.hide()

    def on_card_click(self, card):
        if self.click_handler is not None:
            self.click_cnt += 1
            self.click_handler(card)

    def on_animation_ready(self, card):
        if self.animation_rdy_handler is not None:
            self.animation_rdy_handler(card)


class MemorySettings(Popup):
    cards_x = NumericProperty(5)
    cards_y = NumericProperty(4)

    def calc_y(self, x):
        ratio = self.width / self.height

        n_x = int(x//1)
        n_y = int(ceil(x/ratio))
        if (n_x * n_y) % 2 == 1:
            n_y += 1
        return n_y


class MemoryScreen(Screen):
    score_label = ObjectProperty()
    click_label = ObjectProperty()
    game_time = NumericProperty()
    timer_event = ObjectProperty()
    table = ObjectProperty()

    def clock_start(self):
        self.game_time = 0
        self.timer_event = Clock.schedule_interval(self.clock_tick, 1)

    def clock_stop(self):
        if self.timer_event is not None:
            self.timer_event.cancel()

    def clock_tick(self, *args):
        self.game_time += 1
        if self.game_time > 20*60:
            self.clock_stop()

    def on_reset(self, *args):
        self.clock_stop()
        self.table.reset_game()
        self.clock_start()
        game_name = 'Memory_%dx%d' % (self.table.cards_x, self.table.cards_y)
        DB.game_name = game_name

    def pair_found(self, *args):
        print('Jeh')

    def on_game_end(self, *args):
        self.clock_stop()
        popup = HighScorePopup(score=self.game_time)
        popup.bind(on_dismiss=self.on_reset)
        popup.open()

    def on_scores(self, *args):
        p = HighScoreViewer()
        p.bind(on_dismiss=self.on_reset)
        p.open()

    def on_enter(self, *args):
        self.on_reset()

    def on_leave(self, *args):
        print('Memory leave')
        self.clock_stop()

    def on_settings(self, *args):
        s = MemorySettings()
        s.cards_x = self.table.cards_x
        s.cards_y = self.table.cards_y
        s.bind(on_dismiss=self.on_apply_settings)
        s.open()

    def on_apply_settings(self, popup, *args):
        self.table.cards_x = int(popup.cards_x)
        self.table.cards_y = int(popup.cards_y)
        self.on_reset()

