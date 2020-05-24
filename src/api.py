import json
import logging
import os
import re
import sys
import time
import web

sys.path.append(os.path.dirname(__file__))

from fabric import fabric, Job
from service import sync
from state import State
from utils import is_int_in_range
import settings


urls = (
    '/game', 'GameCreate',
    '/game/([a-zA-Z]{5})', 'GamePoll',
    '/game/([a-zA-Z]{5})/join', 'GameJoin',
    '/game/([a-zA-Z]{5})/start', 'GameStart',
    '/game/([a-zA-Z]{5})/play', 'GamePlay',
    '/game/([a-zA-Z]{5})/options', 'GameOptions',
    '/word/([a-zA-Z]{2,15})', 'WordInfo',
)

web.config.debug = False


class GameCreate(object):
    def POST(self):
        data = json.loads(web.data() or '{}')
        link = data.get('link', None)
        if link is not None:
            link = str(link)
            if len(link) > 5:
                return '{"error":"invalid link"}'
        return sync.create(None, [link], as_json=True)


class GameJoin(object):
    def POST(self, name):
        data = json.loads(web.data() or '{}')
        handle = data.get('handle', None)
        if not handle:
            return '{"error":"handle missing"}'
        if len(handle) > 25:
            return '{"error":"handle too long"}'
        return sync.join(name, [handle], as_json=True)


class GamePoll(object):
    def GET(self, name):
        data = web.input() or {}
        step = data.get('step', None)

        try:
            if step is not None:
                step = int(step)
        except ValueError:
            return '{"error":"Step should be integer."}'

        state = State()
        if not state.load(name):
            return '{"error":"Game not found."}'

        if step is None or state.step > step:
            return json.dumps(state.cleaned())
        else:
            return fabric.wait('channel:' + name, timeout=600)


class GameStart(object):
    def POST(self, name):
        data = json.loads(web.data() or '{}')
        nonce = data.get('nonce', None)
        if not nonce:
            return '{"error":"nonce missing"}'
        return sync.start(name, [nonce], as_json=True)


class GamePlay(object):
    def POST(self, name):
        data = json.loads(web.data() or '{}')
        nonce = data.get('nonce', None)
        if not nonce:
            return '{"error":"nonce missing"}'

        word = data.get('word', None)
        if not word:
            return '{"error":"word missing"}'
        word = word.upper()

        if not re.match(r'^[A-Z]', word):
            return '{"error":"Invalid characters"}'

        return sync.play(name, [nonce, word], as_json=True)


class GameOptions(object):
    def POST(self, name):
        data = json.loads(web.data() or '{}')

        nonce = data.get('nonce', None)
        if not nonce:
            return '{"error":"nonce missing"}'

        bot_level = data.get('bot_level', None)
        if not is_int_in_range(bot_level, 0, 5):
            return '{"error","Invalid bot level"}'

        min_word = data.get('min_word', None)
        if not is_int_in_range(min_word, 3, 7):
            return '{"error","Invalid min word"}'

        game_length = data.get('game_length', None)
        if not is_int_in_range(game_length, 1, 3):
            return '{"error","Invalid game length"}'

        ruleset = data.get('ruleset', None)
        if not is_int_in_range(ruleset, 1, 2):
            return '{"error","Invalid rule set"}'

        return sync.set_options(name, [
            nonce,
            bot_level,
            min_word,
            game_length,
            ruleset,
        ], as_json=True)


class WordInfo(object):
    def GET(self, word):
        return sync.word_info(None, [word.upper()], as_json=True)


class SnatchMiddleware(object):
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger('api')

    def __call__(self, environ, start_response):

        def custom_start_response(status, headers, exc_info=None):
            headers.append(('Access-Control-Allow-Origin', '*'))
            headers.append(('Content-Type', 'application/json'))
            return start_response(status, headers, exc_info)

        try:
            start_time = time.time()
            for event in self.app(environ, custom_start_response):
                yield event
        finally:
            end_time = time.time()
            qs = environ.get('QUERY_STRING', '')
            if qs:
                qs = '?' + qs
            self.logger.info('%0.04f | %s %s%s' % (
                end_time - start_time,
                environ.get('REQUEST_METHOD'),
                environ.get('PATH_INFO'),
                qs,
            ))


app = web.application(urls, globals())


if __name__ == '__main__':
    app.run(SnatchMiddleware)
else:
    application = app.wsgifunc(SnatchMiddleware)
