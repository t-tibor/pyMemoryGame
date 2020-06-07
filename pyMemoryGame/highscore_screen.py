from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup

from pyMemoryGame.highscore_database import DB


class HighScoreTable(GridLayout):
    def __init__(self, **kwargs):
        super(HighScoreTable, self).__init__(**kwargs)

        self.cols = 3
        self.padding = 10
        self.spacing = 10
        self.size_hint = (None, None)
        self.width = 500

        self.bind(minimum_height=self.setter('height'))

        for pos, name, score in DB.scores():
            self.add_widget(Label(text=str(pos+1)))

            self.add_widget(Button(text=str(name), size=(350, 40),
                         size_hint=(None, None)))

            self.add_widget(Button(text=str(score), size=(40, 40)))


def create_score_viewer():
    scroll = ScrollView(size_hint=(None, 1), width=500,
                        pos_hint={'center_x': .5, 'center_y': .5}, do_scroll_x=False)
    scroll.add_widget(HighScoreTable())
    return scroll


class HighScorePopup(Popup):
    def __init__(self, **kwargs):
        super(HighScorePopup, self).__init__()

        self.background_color = (0, 0, 0, 0.2)
        self.auto_dismiss = False

        self._score = kwargs.get('score', 0)
        self._game_name = kwargs.get('game_name', 'Default')
        self.title = '%s: %d' % (self._game_name, self._score)

        main_box = BoxLayout(orientation='vertical', spacing=10, padding=10)

        header_box = BoxLayout(spacing=10, padding=10, size_hint=(1, 0.1))
        header_box.add_widget(Button(text='Cancel', size_hint=(0.2, 1),
                              on_release=self.dismiss))
        self._name_input = TextInput(size_hint=(0.8, 1),
                                        multiline=False)
        header_box.add_widget(self._name_input)
        header_box.add_widget(Button(text='OK', size_hint=(0.2, 1),
                                     on_release=self.add_score))
        main_box.add_widget(header_box)

        main_box.add_widget(create_score_viewer())

        self.content = main_box

    def add_score(self, *args):
        DB.add_score(self._name_input.text, self._score)
        self.dismiss()


class HighScoreViewer(Popup):
    def __init__(self, **kwargs):
        super(HighScoreViewer, self).__init__()
        self.title = 'High scores'

        main_box = BoxLayout(orientation='vertical')
        main_box.add_widget(create_score_viewer())

        footer = AnchorLayout(anchor_x='center', anchor_y='bottom', size_hint=(1, None), height=70)
        footer.add_widget(Button(size_hint=(None, None), size=(70, 70), background_normal='./icons/apply.png',
                                 on_press=self.close))
        main_box.add_widget(footer)
        self.content = main_box

    def close(self, *args):
        self.dismiss()

