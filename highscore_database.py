import datetime
import json
import os

from kivy.event import EventDispatcher
from kivy.properties import StringProperty


class ScoreDatabase(EventDispatcher):
    game_name = StringProperty('Default')

    def __init__(self, path):
        self.dbs = dict()
        self.db = []
        self._path = path
        self.load_from_file()

        self.bind(game_name=self.checkout_db)

    def checkout_db(self, source, game_name, *args):
        self.db = self.dbs.get(game_name, list())
        self.game_name = game_name
        self._sort_db()
        self._chop_db()

    def _sort_db(self):
        self.db.sort(key=lambda item: item['score'], reverse=False)

    def _chop_db(self):
        self.db = self.db[0:20]

    def commit_db(self):
        self._sort_db()
        self._chop_db()
        self.dbs[self.game_name] = self.db

    def commit_and_push_db(self):
        self.commit_db()
        self.save_to_file()

    def add_score(self, name, score):
        item = dict(name=name, score=score, date=datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S'))
        self.db.append(item)
        self.commit_and_push_db()

    def load_from_file(self):
        if not os.path.exists(self._path):
            with open(self._path, 'w') as f:
                json.dump([], f)

        with open(self._path, 'r') as f:
            self.dbs = json.load(f)

    def save_to_file(self):
        with open(self._path, 'w') as f:
            json.dump(self.dbs, f)

    def scores(self):
        for idx, item in enumerate(self.db):
            yield idx, item['name'], item['score']


DB = ScoreDatabase(r'./pyMemoryDb.json')
