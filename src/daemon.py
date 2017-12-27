import json

from fabric import fabric
from game import Game
import settings


class Client(object):
    def __init__(self):
        pass


class Daemon(object):

    def __init__(self):
        self.running = True
        # XXX: write better interupt code

    def run_forever(self):
        while self.running:
            job = fabric.poll_job(settings.QUEUE_NAME)
            print 'JOB:', job.data
            try:
                Game.execute(job)
            except Exception, e:
                import traceback
                print traceback.format_exc()


if __name__ == '__main__':
    Daemon().run_forever()
