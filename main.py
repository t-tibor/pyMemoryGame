import kivy
kivy.require('1.2.0')
from kivy.app import App
from video_player import VideoScreen
from memory_screen import MemoryScreen

from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout






class MainScreen(Screen):
    pass


class SchoolApp(App):
    def build(self):

        sm = ScreenManager()

        sm.add_widget(MainScreen())
        sm.add_widget(VideoScreen())
        sm.add_widget(MemoryScreen())
        return sm



if __name__ == '__main__':
    SchoolApp().run()