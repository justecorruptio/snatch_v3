import json
import web

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
        job = Job(action='start', name=name)
        fabric.defer_job(settings.QUEUE_NAME, job)
        return json.dumps(job.result)

class GamePlay(object):
    def POST(self, name):
        return '{}'

if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()
