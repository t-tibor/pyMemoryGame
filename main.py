import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivy.config import Config
Config.set('graphics', 'multisamples', '0')
Config.set("kivy", "keyboard_mode", "dock")
Config.set("graphics", "fullscreen", "auto")
import kivy
kivy.require('1.2.0')
from kivy.app import App
from video_player import VideoScreen
from memory_screen import MemoryScreen

from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from utils import *


class MainScreen(Screen):
    pass


class SchoolApp(App):
    watchdog_time_left = NumericProperty()
    watchdog_event = ObjectProperty()
    screenManager = ObjectProperty()

    watchdog_tick_period_sec = 60
    watchdog_timeout_sec = 10*60

    def build(self):

        self.screenManager = sm = ScreenManager()
        self.watchdog_event = Clock.schedule_interval(self.watchdog_tick, self.watchdog_tick_period_sec)
        self.watchdog_reset()

        sm.bind(on_touch_down=self.touch_handler)

        sm.add_widget(MainScreen())
        sm.add_widget(VideoScreen())
        sm.add_widget(MemoryScreen())
        return sm

    def watchdog_reset(self):
        self.watchdog_time_left = self.watchdog_timeout_sec

    def touch_handler(self, *args):
        self.watchdog_reset()
        print('Touch happened.')

    def watchdog_tick(self, *args):
        self.watchdog_time_left -= self.watchdog_tick_period_sec
        if self.watchdog_time_left < 0:
            self.watchdog_reset()
            print('Watchdog reset')
            self.screenManager.current = 'Main'


if __name__ == '__main__':
    SchoolApp().run()