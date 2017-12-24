from collections import namedtuple
import json
import random
from redis import StrictRedis
from string import digits, ascii_uppercase
import time

import settings


PHASE_LOBBY = 1
PHASE_STARTED = 2
PHASE_ENDGAME = 3
PHASE_ENDED = 4

NAME_CHARS = ascii_uppercase


State = namedtuple('State', ['phase', 'step', 'start_ts', 'bag', 'table', 'players', 'nonce'])
''' **** SCHEMA ****
    phase: phase number
    step: vector clock
    start_ts: start_ts of this phase
    bag: list of letters
    table: list of words
    players: list of (name, words) tuples
    nonce: dict mapping nonce key to player number
'''


class Game(object):

    def __init__(self, name=None):
        self.name = name
        self.state = None
        self.redis = StrictRedis(**settings.REDIS)

    def reset(self):
        bag = list(settings.SCRABBLE_LETTERS)
        random.shuffle(bag)
        self.state = State(
            phase=PHASE_LOBBY,
            step=0,
            start_ts=time.time(),
            bag=''.join(bag),
            table=[],
            players=[],
            nonce={},
        )

    @classmethod
    def create(cls):
        game = cls()
        game.reset()
        success = False
        while not success:
            game.name = ''.join(random.choice(NAME_CHARS) for i in xrange(5))
            success = game.store(initial=True)
        return game

    @property
    def redis_key(self):
        return 'game:%s' % (self.name,)

    def store(self, initial=False):
        serialized = json.dumps(self.state)
        success = self.redis.set(self.redis_key, serialized, nx=initial)
        if success and initial:
            self.redis.expire(self.redis_key, settings.GAME_TTL)
        return success

    def load(self):
        serialized = self.redis.get(self.redis_key)
        self.state = State(*json.loads(serialized))

if __name__ == '__main__':
    game = Game.create()
    print game.name

    game.load()
    print game.state
