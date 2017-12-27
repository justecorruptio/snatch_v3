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


class State(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


''' **** SCHEMA ****
    phase: phase number
    step: vector clock
    start_ts: start_ts of this phase
    bag: list of letters
    table: list of words
    players: list of (name, words) tuples
    nonces: dict mapping nonce key to player number
'''

def rand_chars(length):
    return ''.join(
        random.choice(ascii_uppercase)
        for i in xrange(length)
    )

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
            table='',
            players=[],
            nonces={},
        )

    @classmethod
    def create(cls):
        game = cls()
        game.reset()
        success = False
        while not success:
            game.name = rand_chars(5)
            success = game.store(initial=True)
        return game

    def join(self, handle):
        next_player_num = len(self.state.players)
        nonce = '%s_%03d' % (rand_chars(7), next_player_num)
        self.state.players.append((handle, []))
        self.state.nonces[nonce] = next_player_num
        return nonce

    def start(self):
        self.state.phase = PHASE_STARTED
        self.state.start_ts = time.time()

    def peel(self):
        self.state.table += self.state.bag[0]
        self.state.bag = self.state.bag[1:]
        if len(self.state.bag) == 0:
            self.state.phase = PHASE_ENDED
            self.state.start_ts = time.time()

    @property
    def game_key(self):
        return 'game:%s' % (self.name,)

    @property
    def lock_key(self):
        return 'lock:%s' % (self.name,)

    def acquire(self):
        return self.redis.set(self.lock_key, '1',
            nx=True, ex=settings.LOCK_TTL,
        )

    def release(self):
        self.redis.delete(self.lock_key)

    def store(self, initial=False):
        serialized = json.dumps(self.state)
        return self.redis.set(self.game_key, serialized,
            nx=initial, ex=settings.GAME_TTL,
        )

    def load(self):
        serialized = self.redis.get(self.game_key)
        self.state = State(**json.loads(serialized))

if __name__ == '__main__':
    game = Game.create()
    print game.name

    game.join('Jay')
    game.join('Amy')

    game.peel()
    game.peel()

    game.store()
    game.load()

    print game.state
