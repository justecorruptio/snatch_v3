import json
import logging
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
        self.logger = logging.getLogger('daemon')
        self.running = True
        # XXX: write better interupt code

    def run_forever(self):
        while self.running:
            job = fabric.poll_job(settings.QUEUE_NAME)
            try:
                start_ts = time.time()
                planned_ts = job.planned_ts
                result = Game.execute(job)
                end_ts = time.time()
            except Exception, e:
                import traceback
                self.logger.error('DATA: ' + str(job.data))
                self.logger.error(traceback.format_exc())
            else:
                self.logger.info(
                    '%0.2f + %0.4f (%0.4f off) | %s -> %s' % (
                        start_ts,
                        end_ts - start_ts,
                        start_ts - planned_ts,
                        job.data,
                        result,
                    ),
                )


if __name__ == '__main__':
    Daemon().run_forever()
