from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import StringProperty, ObjectProperty, NumericProperty
from kivy.uix.dropdown import DropDown


class ScreenFooter(AnchorLayout):
    transition_dir = StringProperty('right')
    screen = ObjectProperty()


class VideoFooter(AnchorLayout):
    transition_dir = StringProperty('right')
    screen = ObjectProperty()

