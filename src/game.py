import json
import random
import time

from fabric import fabric, Job
import settings
from utils import rand_chars


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


class Game(object):

    def __init__(self, name=None):
        self.name = name
        self.state = None

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
        if any(p[0] == handle for p in self.state.players):
            return {'error': 'duplicate name'}
        next_player_num = len(self.state.players)
        nonce = '%s_%03d' % (rand_chars(7), next_player_num)
        self.state.players.append((handle, []))
        self.state.nonces[nonce] = next_player_num
        return {'nonce': nonce}

    def start(self):
        self.state.phase = PHASE_STARTED
        self.state.start_ts = time.time()

    def peel(self):
        self.state.table += self.state.bag[0]
        self.state.bag = self.state.bag[1:]
        if len(self.state.bag) == 0:
            self.state.phase = PHASE_ENDGAME
            self.state.start_ts = time.time()

    def end(self):
        self.state.phase = PHASE_ENDED
        self.state.start_ts = time.time()

    def play(self, nonce, word):
        player_num = self.state.nonces.get(none, None)
        if player_num is None:
            return {'error': 'invalid player'}

        return {}

    @classmethod
    def execute(cls, job):
        action = job.data['action']
        if action == 'create':
            game = cls.create()
            job.write_result({'name': game.name})
            return
        name = job.data['name']
        args = job.data.get('args', [])
        game = cls(name)

        try:
            has_lock = False
            has_lock = fabric.acquire(game.lock_key)
            if not has_lock:
                job.retry()
                return

            game.load()
            try:
                result = getattr(game, action)(*args)
            except Exception, e:
                result = {'error': e}
            job.write_result(result)
            game.store()

        finally:
            if has_lock:
                fabric.release(game.lock_key)

    @property
    def game_key(self):
        return 'game:%s' % (self.name,)

    @property
    def lock_key(self):
        return 'lock:%s' % (self.name,)

    def store(self, initial=False):
        serialized = json.dumps(self.state)
        return fabric.store(self.game_key, serialized,
            nx=initial, ex=settings.GAME_TTL,
        )

    def load(self):
        serialized = fabric.load(self.game_key)
        self.state = State(**json.loads(serialized))

'''
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
'''
