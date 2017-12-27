import json
import sys
import time

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
            try:
                start_ts = time.time()
                Game.execute(job)
                end_ts = time.time()
            except Exception, e:
                if settings.DEBUG:
                    import traceback
                    sys.stderr.write('ERROR! ' + str(job.data) + '\n')
                    sys.stderr.write(traceback.format_exc() + '\n')
            else:
                if settings.DEBUG:
                    sys.stderr.write('%0.2f + %0.4f | %s\n' % (
                        start_ts,
                        end_ts - start_ts,
                        job.data,
                    ))


if __name__ == '__main__':
    Daemon().run_forever()
