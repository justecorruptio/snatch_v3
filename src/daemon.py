import json
import logging
import signal
import sys
import time

from fabric import fabric
from game import Game
import settings


class Daemon(object):

    def __init__(self):
        self.logger = logging.getLogger('daemon')
        self.running = True

        def _sig_handler(signum, frame):
            self.running = False

        signal.signal(signal.SIGTERM, _sig_handler)

    def run_forever(self):
        self.logger.info('Starting Server.')

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

        self.logger.info('Stopping Server.')


if __name__ == '__main__':
    Daemon().run_forever()
