import json
import sys

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
            if settings.DEBUG:
                sys.stderr.write('JOB: ' + str(job.data) + '\n')
            try:
                Game.execute(job)
            except Exception, e:
                if settings.DEBUG:
                    import traceback
                    sys.stderr.write(traceback.format_exc() + '\n')


if __name__ == '__main__':
    Daemon().run_forever()
