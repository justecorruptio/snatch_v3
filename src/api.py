import json
import os
import sys
import web

sys.path.append(os.path.dirname(__file__))

from fabric import fabric, Job
from service import sync
import settings


urls = (
    '/game', 'GameCreate',
    '/game/([a-zA-Z]{5})', 'GamePoll',
    '/game/([a-zA-Z]{5})/join', 'GameJoin',
    '/game/([a-zA-Z]{5})/start', 'GameStart',
    '/game/([a-zA-Z]{5})/play', 'GamePlay',
    '/game/([a-zA-Z]{5})/addBot', 'GameAddBot',
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
        if step is None:
            # TODO: call state.load directly
            return sync.fetch(name, as_json=True)
        else:
            return fabric.wait('channel:%s' % (name,), timeout=600)


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
        return sync.play(name, [nonce, word], as_json=True)


class GameAddBot(object):
    def POST(self, name):
        data = json.loads(web.data() or '{}')
        nonce = data.get('nonce', None)
        if not nonce:
            return '{"error":"nonce missing"}'

        level = data.get('level', None)
        if not level:
            return '{"error":"level missing"}'

        # TODO: make this a start() option
        return sync.add_bot(name, [nonce, level], as_json=True)


class HeadersMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):

        def custom_start_response(status, headers, exc_info=None):
            headers.append(('Access-Control-Allow-Origin', '*'))
            headers.append(('Content-Type', 'application/json'))
            return start_response(status, headers, exc_info)

        return self.app(environ, custom_start_response)


app = web.application(urls, globals())


if __name__ == '__main__':
    app.run(HeadersMiddleware)
else:
    application = app.wsgifunc(HeadersMiddleware)
