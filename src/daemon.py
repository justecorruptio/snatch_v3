import json

from fabric import Fabric
from game import Game
import settings


class Client(object):
    def __init__(self):
        pass


class Daemon(object):

    def __init__(self):
        self.fabric = Fabric()
        self.running = True
        # XXX: write better interupt code

    def run_forever(self):
        while self.running:
            message = self.fabric.poll(settings.QUEUE_NAME)
            name, action, args = json.loads(message)
            game = Game(name)


if __name__ == '__main__':
    SnatchDaemon().run_forever()
