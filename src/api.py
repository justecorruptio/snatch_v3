import json
import web

from fabric import fabric, Job
import settings

urls = (
    '/game', 'Game',
    '/game/([a-zA-Z]{5})/join', 'GameJoin',
    '/game/([a-zA-Z]{5})/play', 'GamePlay',
)

web.config.debug = False

class Game(object):
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

class GamePlay(object):
    def POST(self, name):
        return '{}'

if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()
