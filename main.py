import random
import os
import functools

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color
from kivy.properties import NumericProperty
from kivy.animation import Animation

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
        v+= 1
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
            yield (x,y)


class Table(FloatLayout):

    score = NumericProperty()
    click_cnt = NumericProperty()

    def reset_game(self, *args):
        random.shuffle(self.Cards)

        space_ratio = 0.1
        full_h_ratio = self.size_x + (self.size_x-1)*space_ratio
        full_w_ratio = self.size_y + (self.size_y - 1) * space_ratio
        for (card, coord) in zip(self.Cards, matrix_pos_generator(self.size_x, self.size_y)):
            pos_x = coord[0]
            pos_y = coord[1]
            card.size_hint = (1.0 / full_h_ratio, 1.0 / full_w_ratio)
            card.pos_hint = {'x': (1.0 + space_ratio) / full_h_ratio * pos_x,
                             'y': (1.0 + space_ratio) / full_w_ratio * pos_y}
            card.reset()

        self.score = 0
        self.click_cnt = 0
        self.click_handler = self._state_empty
        self.animation_rdy_handler = None

    def __init__(self, size_x, size_y, picture_list, **kwargs):
        super(FloatLayout, self).__init__(**kwargs)

        self.size_x = size_x
        self.size_y = size_y
        self.cardCount = size_x * size_y
        if self.cardCount % 2 == 1:
            raise Exception('Invalid card count')
        self.picture_list = picture_list
        if self.cardCount/2 > len(picture_list):
            raise Exception('Not enough picture given. Need: %d, has: %d' % (self.cardCount/2, len(picture_list)))

        self.selected1 = None
        self.selected2 = None
        self.cardsLeft = size_x * size_y
        self.score = 0
        self.click_cnt = 0

        keys = list(range(int(self.cardCount/2)))*2
        random.shuffle(keys)
        self.Cards = [SimpleCard(self, key, picture_list[key]) for key in keys]
        for card in self.Cards:
            self.add_widget(card)

        self.click_handler = self._state_empty
        self.animation_rdy_handler = None
        self.reset_game()

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
                self.cardsLeft -= 2
                self.score += 1

                print('Pair found')
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


def load_pictures(path='./pictures'):
    if not os.path.isdir(path):
        raise Exception('Given folder: %s does not exists' % path)
    file_list = [os.path.join(path, fname) for fname in os.listdir(path) if fname.endswith('.png') or fname.endswith('.jpg')]
    random.shuffle(file_list)
    return file_list


class MemoryApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical')
        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        restart_button = Button(text='Restart')
        click_label = Label(text='Clicks: 0')
        score_label = Label(text='Score: 0')
        header.add_widget(click_label)
        header.add_widget(restart_button)
        header.add_widget(score_label)

        table = Table(5, 4, load_pictures())

        def update_score(label, game_table, *argc):
            label.text = 'Score: %d' % game_table.score

        def update_clicks(label, game_table, *argc):
            label.text = 'Clicks: %d' % game_table.click_cnt

        restart_button.bind(on_touch_down=table.reset_game)
        table.bind(score=functools.partial(update_score, score_label, table))
        table.bind(click_cnt=functools.partial(update_clicks, click_label, table))

        root.add_widget(header)
        root.add_widget(table)

        return root


if __name__ == '__main__':

    MemoryApp().run()
