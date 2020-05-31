import os.path
from sys import argv
from os.path import dirname, join
from kivy.uix.video import Video
from kivy.uix.videoplayer import VideoPlayer
import kivy
from ffpyplayer.player import MediaPlayer
from ffpyplayer.writer import MediaWriter
import time
import pathlib
import logging
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage, Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Rectangle, Line, Color
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from utils import *
import functools

kivy.require('1.2.0')


class CustomLoggerAdapter(logging.LoggerAdapter):
    """
    This example adapter expects the passed in dict-like object to have a
    'connid' key, whose value in brackets is prepended to the log message.
    """
    def process(self, msg, kwargs):
        return '%s:%s' % (self.extra['modname'], msg), kwargs


video_logger_base = logging.getLogger('kivy.VideoPlayer')
video_logger = CustomLoggerAdapter(video_logger_base, {'modname': 'VideoPlayer'})


class VideoDatabase:
    def __init__(self):
        video_logger.info('Discovering available videos.')
        video_dir = os.path.join(os.path.dirname(__file__), 'videos')
        if not os.path.exists(video_dir):
            raise Exception('Missing video directory with path: %s' % video_dir)

        self._videos = list()

        files = os.listdir(video_dir)
        video_files = [pathlib.Path(os.path.join(video_dir, f)) for f in files if f.endswith('.mp4')]
        image_files = [pathlib.Path(os.path.join(video_dir, f)) for f in files if f.endswith('.png')]

        for video_path in video_files:
            video_logger.info('Video found: %s' % str(video_path))
            match_img = video_path.with_suffix('.png')
            if match_img not in image_files:
                video_logger.info('Generating thumbnail.')
                VideoDatabase.generate_thumbnail(str(video_path))
            else:
                video_logger.info('Thumbnail exists.')
            self._videos.append({'video_path': video_path, 'thumbnail_path': match_img})

    def get_video_count(self):
        return len(self._videos)

    def videos(self):
        for d in self._videos:
            yield (str(d['video_path']), str(d['thumbnail_path']))

    @staticmethod
    def generate_thumbnail(video_path):
        ff_opts = {'an': True, 'sync': 'video'}
        player = MediaPlayer(video_path, ff_opts=ff_opts)
        while player.get_metadata()['src_vid_size'] == (0, 0):
            time.sleep(0.01)
        metadata = player.get_metadata()
        frame_size = metadata['src_vid_size']
        fmt = player.get_output_pix_fmt()

        player.seek(4.0)
        while True:
            frame, val = player.get_frame()
            if frame is not None:
                img = frame[0]
                ts = frame[1]
                if ts > 3:
                    break
            else:
                time.sleep(0.1)
        player.set_pause(True)

        width_out = 640
        resize_ratio = width_out / frame_size[0]
        height_out = frame_size[1] * resize_ratio
        out_opts = {'pix_fmt_in': fmt, 'width_in': frame_size[0],
                    'height_in': frame_size[1], 'codec': 'png',
                    'frame_rate': (30, 1), 'width_out': width_out,
                    'height_out': height_out}
        output_name = str(pathlib.Path(video_path).with_suffix('.png'))
        writer = MediaWriter(output_name, [out_opts])
        writer.write_frame(img=img, pts=0, stream=0)
        writer.close()

        player.close_player()


DB = VideoDatabase()


class Player(Popup):
    def __init__(self, **kwargs):
        super(Player, self).__init__()

        self.background_color = (0, 0, 0, 0.2)
        self.video_path = kwargs.get('video_path', None)
        self.auto_dismiss = False
        self.title = 'Video: %s' % (kwargs.get('video_name', ''))

        self.player = VideoPlayer(source=kwargs.get('video_path', ''), thumbnail=kwargs.get('thumbnail_path'), state='play')
        self.content = self.player

        self.player.bind(state=self.exit)

    def exit(self, *args, **kwargs):
        if self.player.state == 'stop':
            self.dismiss()
        logging.info('Video state changed')


class VideoIcon(Image):
    def __init__(self, thumbnail_path, video_path='', **kwargs):
        super(VideoIcon, self).__init__(**kwargs)
        self.source = thumbnail_path

        self.video_attrs = dict()
        self.video_attrs['thumbnail_path'] = thumbnail_path
        self.video_attrs['video_path'] = video_path
        self.video_attrs['video_name'] = pathlib.Path(video_path).name
        self.video_attrs['widget'] = self
        self.register_event_type('on_video_selected')

        self._border = Line(rectangle=(*self.pos, *self.size), width=0)
        self._border.width = 9
        self._border.dash_length = 1
        self._border.dash_offset = 0
        self.canvas.before.add(Color(0, 0, 1, 0.4))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dispatch('on_video_selected', **self.video_attrs)
            return True
        return False

    def on_video_selected(self, *args, **kwargs):
        print('Video selected: %s', kwargs.get('video_path', ''))

    def highlight(self):
        self._border.rectangle = (*self.pos, *self.size)
        self.canvas.before.add(self._border)

    def de_highlight(self):
        if self._border:
            self.canvas.before.remove(self._border)


class VideoGrid(GridLayout):
    def __init__(self, **kwargs):
        super(VideoGrid, self).__init__(**kwargs)

        self.cols = 3
        self.padding = 10
        self.spacing = 10

        self._video_icons = list()
        self._selected_video = None

        self.register_event_type('on_selection_changed')

        for video_path, thumbnail_path in DB.videos():
            icon = VideoIcon(thumbnail_path=thumbnail_path, video_path=video_path)
            icon.bind(on_video_selected=self.video_selected)
            icon.size_hint_y = None
            icon.height = 200
            self._video_icons.append(icon)
            self.add_widget(icon)

    def video_selected(self, *args, **kwargs):
        if self._selected_video:
            self._selected_video.de_highlight()
        self._selected_video = kwargs.get('widget', None)
        if self._selected_video:
            self._selected_video.highlight()

        self.dispatch('on_selection_changed', self._selected_video.video_attrs)

    def on_selection_changed(self, *args, **kwargs):
        pass

    def get_selected_video(self):
        if self._selected_video:
            return self._selected_video.video_attrs
        return None


class VideoGridWrapper(BoxLayout):
    def __init__(self, **kwargs):
        super(VideoGridWrapper, self).__init__(**kwargs)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_y=True)
        scroll.add_widget(VideoGrid())
        self.add_widget(scroll)


class VideoScreen(Screen):
    grid = ObjectProperty()
    video_label = ObjectProperty()

    def video_selected(self, source, attrs):
        self.video_label.text = attrs.get('video_name', '')

    def on_play(self, *args, **kwargs):
        video_attrs = self.grid.get_selected_video()
        if video_attrs is not None:
            player = Player(**video_attrs)
            player.open()

    def on_back(self, *args, **kwargs):
        self.manager.transition.direction = 'left'
        self.manager.current = 'Main'
