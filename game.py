import json
import random
from redis import StrictRedis

import settings


STATE_LOBBY = 10
STATE_STARTED = 20
STATE_ENDGAME = 30
STATE_ENDED = 40

REDIS_GAME_FORMAT = 'game:%s'

NAME_CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

''' ****REDIS SCHEMA****

game:ABCDEF => JSON({
    state: 10,
    step: 0,
    phase_elapse: 24,
    bag: 'AAABBCC...',
    table: 'JHYREP...',
    players: {
        '<nonce>': {
            name: 'Albert',
            words: ['FOVIA', ...],
        }
    },
})

'''

class State(object):
    __slots__ = [
        'state',
        ste


class Game(object):

    def __init__(self):
        #self.state = STATE_LOBBY
        #self.bag = settings.SCRABBLE_LETTERS

        self.name = None
        self.redis = StrictRedis(**settings.REDIS)

    @classmethod
    def create(cls):
        game = cls()
        while True:
            name = ''.join(random.choice(NAME_CHARS) for i in xrange(6))
            if game.redis.setnx(REDIS_GAME_FORMAT % (name,), ''):
                break

        game.redis.expire(REDIS_GAME_FORMAT % (name,), settings.GAME_TTL)
        game.name = name
        return game

    def load(self):
        pass

    def store(self):
        pass

if __name__ == '__main__':
    game = Game.create()
    print game.name
