import json
import random
import sys
import time

from anagram import anagram
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

    def cleaned(self):
        ret = dict(self)
        if 'nonces' in ret:
            ret.pop('nonces')
        if 'bag' in ret:
            ret['bag'] = len(ret['bag'])
        if 'start_ts' in ret:
            ret['time_left'] = (
                settings.ENDGAME_TIME - (time.time() - ret['start_ts'])
            )
        return ret


''' **** SCHEMA ****
    phase: phase number
    step: vector clock
    start_ts: start_ts of this phase
    bag: list of letters
    table: string of letters
    log: list of log messages, recent last
    players: list of (name, words) tuples
    nonces: dict mapping nonce key to player number
'''


class Game(object):

    def __init__(self, name=None):
        self.name = name
        self.state = None

    def reset(self):
        self.state = State(
            phase=PHASE_LOBBY,
            step=0,
            start_ts=time.time(),
            bag=settings.LETTERS,
            table='',
            log=[],
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

    def join(self, handle, nonce=None):
        if any(p[0] == handle for p in self.state.players):
            return {'error': 'duplicate name'}
        next_player_num = len(self.state.players)
        if nonce is None:
            nonce = '%s_%03d' % (rand_chars(7), next_player_num)
        self.state.players.append((handle, []))
        self.state.nonces[nonce] = next_player_num
        self.state.step += 1

        self.log('join', handle)

        return {'nonce': nonce}

    def start(self, nonce):

        player_num = self.state.nonces.get(nonce, None)
        if player_num is None:
            return {'error': 'invalid player'}

        self.state.phase = PHASE_STARTED
        self.state.start_ts = time.time()
        self.state.step += 1

        self.log('start')

        fabric.defer_job(
            settings.QUEUE_NAME,
            Job(action='peel', name=self.name),
            delay=settings.PEEL_DELAY,
        )

        if 'BOT' in self.state.nonces:
            fabric.defer_job(
                settings.QUEUE_NAME,
                Job(action='loop_bot', name=self.name),
            )

        return {}

    def peel(self):
        letter = random.choice(self.state.bag)
        self.state.table = self.state.table + letter
        bag = list(self.state.bag)
        bag.remove(letter)
        self.state.bag = ''.join(bag)
        self.state.step += 1

        if len(self.state.bag) == 0:
            self.state.phase = PHASE_ENDGAME
            self.state.start_ts = time.time()
            self.log('endgame')
            # calling this now is guaranteed to not actually end
            self.end()
        else:
            fabric.defer_job(
                settings.QUEUE_NAME,
                Job(action='peel', name=self.name),
                delay=settings.PEEL_DELAY,
            )

        return None

    def end(self):
        delayed_time = time.time() - self.state.start_ts
        if delayed_time < settings.ENDGAME_TIME:
            fabric.defer_job(
                settings.QUEUE_NAME,
                Job(action='end', name=self.name),
                # fix a tiny race condition
                delay=settings.ENDGAME_TIME - delayed_time + .01,
            )
            return

        self.state.phase = PHASE_ENDED
        self.state.start_ts = time.time()
        self.state.step += 1
        self.log('end')

        return None

    def play(self, nonce, target, how=None):
        player_num = self.state.nonces.get(nonce, None)
        if player_num is None:
            return {'error': 'Invalid player'}

        if len(target) < settings.MIN_WORD_LENGTH:
            return {'error': 'Minimum word length is %s' % (
                settings.MIN_WORD_LENGTH,
            )}

        if not anagram.is_word(target):
            return {'error': '%s is not a word' % (target,)}

        if how is None:
            how, error = anagram.check(
                self.state.table,
                sum([words for _, words in self.state.players], []),
                target,
            )

        if how is None:
            return {'error': error}

        status = None
        for w in how:
            for i, (_, words) in enumerate(self.state.players):
                if w in words:
                    words.remove(w)
                    status = ('steal', target, player_num, w, i)
                    break
            # table and player words are mutually exclusive.
            if w in self.state.table:
                table = list(self.state.table)
                table.remove(w)
                self.state.table = ''.join(table)

        if not status:
            status = ('play', target, player_num)

        self.state.players[player_num][1].append(target)
        self.state.step += 1

        self.log(*status)

        if self.state.phase == PHASE_ENDGAME:
            self.state.start_ts = time.time()

        return {}

    def add_bot(self, nonce, level):
        player_num = self.state.nonces.get(nonce, None)
        if player_num is None:
            return {'error': 'Invalid player'}

        try:
            level = int(level)
            if level > 5 or level < 1:
                raise Exception()
            level -= 1
        except Exception:
            return {'error', 'Invalid level'}

        if 'BOT' in self.state.nonces:
            return {'error', 'Only one bot per game.'}

        handle = [
            h for h, (l, _, _) in settings.BOTS.items()
            if l == level
        ][0]

        self.join(handle, nonce='BOT')

        return {}

    def loop_bot(self):
        if self.state.phase == 4:
            return {}

        player_num = self.state.nonces['BOT']
        handle = self.state.players[player_num][0]
        level, loop_ttl, max_word_len = settings.BOTS[handle]

        if self.state.phase in (2, 3):
            target, how = anagram.bot(
                self.state.table,
                sum([words for _, words in self.state.players], []),
                max_word_len,
            )

            if target:
                self.play('BOT', target, how)

        fabric.defer_job(
            settings.QUEUE_NAME,
            Job(action='loop_bot', name=self.name),
            delay=loop_ttl,
        )

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

            try:
                game.load()
                start_step = game.state.step

                result = getattr(game, action)(*args)
            except Exception, e:
                import traceback
                sys.stderr.write(traceback.format_exc() + '\n')
                result = {'error': str(e)}

            if result is not None:
                job.write_result(result)

            end_step = game.state.step
            game.store()

            if start_step != end_step:
                fabric.notify(
                    game.channel_key,
                    json.dumps(game.state.cleaned()),
                )

        finally:
            if has_lock:
                fabric.release(game.lock_key)

        return result

    def log(self, *message):
        self.state.log = self.state.log[-4:] + [
            (self.state.step,) + tuple(message),
        ]

    @property
    def game_key(self):
        return 'game:%s' % (self.name,)

    @property
    def lock_key(self):
        return 'lock:%s' % (self.name,)

    @property
    def channel_key(self):
        return 'channel:%s' % (self.name,)

    def store(self, initial=False):
        serialized = json.dumps(self.state)
        return fabric.store(self.game_key, serialized,
            nx=initial, ex=settings.GAME_TTL,
        )

    def load(self):
        serialized = fabric.load(self.game_key)
        if serialized is None:
            raise Exception('game not found')
        self.state = State(**json.loads(serialized))
