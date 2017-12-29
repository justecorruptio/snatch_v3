import json
import os
import sys
import web

sys.path.append(os.path.dirname(__file__))

from fabric import fabric, Job
from game import Game
import settings


urls = (
    '/game', 'GameCreate',
    '/game/([a-zA-Z]{5})', 'GamePoll',
    '/game/([a-zA-Z]{5})/join', 'GameJoin',
    '/game/([a-zA-Z]{5})/start', 'GameStart',
    '/game/([a-zA-Z]{5})/play', 'GamePlay',
)

web.config.debug = False

class GameCreate(object):
    def POST(self):
        job = Job(action='create')
        fabric.defer_job(settings.QUEUE_NAME, job)
        return json.dumps(job.result)

class GameJoin(object):
    def POST(self, name):
        data = json.loads(web.data())
        handle = data.get('handle', None)
        if not handle:
            return '{"error":"handle missing"}'
        job = Job(action='join', name=name, args=[handle])
        fabric.defer_job(settings.QUEUE_NAME, job)
        return json.dumps(job.result)

class GamePoll(object):
    def GET(self, name):
        data = web.input()
        step = data.get('step', None)
        if step is None:
            game = Game(name)
            game.load()
            return json.dumps(game.state.cleaned())
        return fabric.wait('channel:%s' % (name,), timeout=60 * 10)

class GameStart(object):
    def POST(self, name):
        data = json.loads(web.data())
        nonce = data.get('nonce', None)
        if not nonce:
            return '{"error":"nonce missing"}'
        job = Job(action='start', name=name, args=[nonce])
        fabric.defer_job(settings.QUEUE_NAME, job)
        return json.dumps(job.result)

class GamePlay(object):
    def POST(self, name):
        data = json.loads(web.data())
        nonce = data.get('nonce', None)
        if not nonce:
            return '{"error":"nonce missing"}'

        word = data.get('word', None)
        if not word:
            return '{"error":"word missing"}'
        word = word.upper()

        job = Job(action='play', name=name, args=[nonce, word])
        fabric.defer_job(settings.QUEUE_NAME, job)
        return json.dumps(job.result)

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
