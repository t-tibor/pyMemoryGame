from kivy.clock import Clock
from kivy.config import Config
from kivy.cache import Cache
from kivy.uix.image import AsyncImage
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.filechooser import *
from .utils import *
import os
import random
import gc


class PictureDatabase(FileSystemAbstract):
    picture_extensions = ['.jpg', '.JPG', '.png']

    def __init__(self):
        self._root = os.path.join(os.path.dirname(__file__), 'pictures')
        if not os.path.isdir(self._root):
            raise Exception('Picture directory not found')
        folders = [p for p in os.listdir(self._root) if self.is_picture_folder(os.path.join(self._root, p))]
        self.db = dict()
        for folder in folders:
            fdb = self.db[folder] = dict()
            fp = fdb['full_path'] = os.path.join(self._root, folder)
            fdb['image_names'] = self.scan_images(fp)
            fdb['image_paths'] = [os.path.join(fp, f) for f in fdb['image_names']]
            fdb['comment'] = 'demo'

    def is_picture_file(self, f):
        for e in self.picture_extensions:
            if f.endswith(e):
                return True
        return False

    def is_picture_folder(self, path):
        if not os.path.isdir(path):
            return False
        pics = self.scan_images(path)
        return len(pics) > 0

    def scan_images(self, folder):
        return [f for f in os.listdir(folder) if self.is_picture_file(f)]

    def get_random_folder(self):
        if len(self.db) == 0:
            return None
        selected_key = random.choice(self.db.keys())
        return self.db[selected_key]['full_path']

    def get_random_images(self, num=10):
        if len(self.db) == 0:
            return []
        selected_folder = random.choice(list(self.db.keys()))
        fdb = self.db[selected_folder]
        images = fdb['image_paths']
        cnt = min(len(images), num)
        return random.sample(images, cnt), selected_folder

    def get_images_from_folder(self, folder):
        fdb = self.db.get(folder, None)
        if fdb is not None:
            return fdb['image_paths']
        else:
            return []

# implementation of file chooser database
    def listdir(self, fn):
        if fn == '\\' or self._root:
            return ['\\' + f for f in list(self.db.keys())]
        else:
            return []

    def getsize(self, fn):
        raise OSError()

    def is_hidden(self, fn):
        return False

    def is_dir(self, fn):
        return False


PDB = PictureDatabase()


class PictureFolderChooser(FileChooserListView):
    def __init__(self, **kwargs):
        kwargs['file_system'] = PDB
        kwargs['path'] = '\\'
        kwargs['dirselect'] = True
        super(PictureFolderChooser, self).__init__(**kwargs)


class PictureBrowser(Screen):
    viewer = ObjectProperty()

    def on_open(self, source, selection, *args):
        if len(selection) < 1:
            return

        if self.viewer:
            path = os.path.basename(selection[0])
            self.viewer.image_source = path
            self.viewer.auto_step = True
            self.manager.transition.direction = 'left'
            self.manager.current = 'PictureViewer'


class DelayedImage(AsyncImage):
    delayed_source = StringProperty()

    def __init__(self, **kwargs):
        super(DelayedImage, self).__init__(**kwargs)

    def trigger_loading(self, *args):
        self.source = self.delayed_source

    def unload(self):
        self.source = ''


class PictureViewer(Screen):
    _carousel_widget = ObjectProperty()
    _carousel_last_idx = NumericProperty(0)
    _comment_widget = ObjectProperty()
    _auto_step_widget = ObjectProperty()
    _timer = ObjectProperty()

    image_source = StringProperty('')
    auto_step = BooleanProperty(True)

    _loaded_folder = StringProperty('')
    _image_list = ObjectProperty()
    _image_idx = NumericProperty(0)

    def __init__(self, **kwargs):
        super(PictureViewer, self).__init__(**kwargs)
        self._timer = Clock.create_trigger(self.do_step, timeout=5)

        Cache.register('kv.loader', limit=5, timeout=5)
        Cache.register('kv.image', limit=20, timeout=5)
        Cache.register('kv.texture', limit=200, timeout=5)

    def on_settings(self, *args):
        pass

    def get_relative_slide_idx(self, rel_idx):
        idx = self._carousel_widget.index
        idx += rel_idx
        slide_cnt = len(self._carousel_widget.slides)
        while idx < 0:
            idx += slide_cnt
        while idx >= slide_cnt:
            idx -= slide_cnt
        return idx

    def load_pictures(self):
        self._timer.cancel()
        if self.image_source == '':
            self._image_list, self._loaded_folder = PDB.get_random_images()
        else:
            self._image_list = PDB.get_images_from_folder(self.image_source)
            self._loaded_folder = self.image_source

        self._carousel_widget.index = 0
        self._carousel_last_idx = 0
        self.load_slide(0)
        self.rearm_timer()

    def load_slide(self, img_idx, slide_rel_idx=0):
        img_cnt = len(self._image_list)
        if img_idx < 0 or img_idx >= img_cnt:
            return

        prev_img_idx = img_idx-1 if img_idx > 0 else img_cnt-1
        curr_img_idx = img_idx
        next_img_idx = img_idx+1 if img_idx < img_cnt-1 else 0

        prev_slide = self._carousel_widget.slides[self.get_relative_slide_idx(slide_rel_idx-1)]
        curr_slide = self._carousel_widget.slides[self.get_relative_slide_idx(slide_rel_idx)]
        next_slide = self._carousel_widget.slides[self.get_relative_slide_idx(slide_rel_idx+1)]

        prev_slide.source = self._image_list[prev_img_idx]
        curr_slide.source = self._image_list[curr_img_idx]
        next_slide.source = self._image_list[next_img_idx]

        self._image_idx = img_idx
        self._carousel_last_idx = self.get_relative_slide_idx(slide_rel_idx)
        self._carousel_widget.load_slide(curr_slide)

# event handlers
    def on_enter(self, *args):
        gc.collect()
        self.load_pictures()
        self.rearm_timer()

    def on_leave(self, *args):
        self.stop_timer()
        gc.collect()

    def on_auto_step(self, *args):
        self.rearm_timer()
        self._auto_step_widget.state = 'normal' if self.auto_step else 'down'

    def _on_right_slide(self):
        self._image_idx = self._image_idx + 1
        if self._image_idx >= len(self._image_list):
            self._image_idx = 0
        self.load_slide(self._image_idx)

    def _on_left_slide(self):
        self._image_idx = self._image_idx-1
        if self._image_idx < 0:
            self._image_idx += len(self._image_list)
        self.load_slide(self._image_idx)

    def on_slide(self, source, idx, *args):
        di = idx - self._carousel_last_idx
        if di < -1:
            di += 3
        if di > 1:
            di -= 3

        if di == 1:
            self._on_right_slide()
        elif di == -1:
            self._on_left_slide()

        self._carousel_last_idx = idx
        self.rearm_timer()

    def on_toggle_bnt(self, source, state, *args):
        self.auto_step = False if state == 'down' else True

    def stop_timer(self):
        self._timer.cancel()

    def rearm_timer(self):
        self._timer.cancel()
        if self.auto_step:
            self._timer()

    def do_step(self, *args):
        if (self.image_source != '') and (self.image_source == self._loaded_folder):
            self._carousel_widget.load_next()
        else:
            if self._image_idx < len(self._image_list)-1:
                self._carousel_widget.load_next()
            else:
                self.load_pictures()



