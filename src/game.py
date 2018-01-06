import json
import random
import sys
import time

from anagram import anagram, easy_anagram
from fabric import fabric, Job
from service import sync, async
import settings
from state import (
    State,
    PHASE_LOBBY,
    PHASE_STARTED,
    PHASE_ENDGAME,
    PHASE_ENDED,
)
from utils import rand_chars


class GameError(Exception):
    pass


''' **** SCHEMA ****
    phase: phase number
    step: vector clock
    start_ts: start_ts of this phase
    bag: list of letters
    table: string of letters
    log: list of log messages, recent last
    players: list of (name, words) tuples
    nonces: dict mapping nonce key to player number
    next_name: name of the next game.
'''


class Game(object):

    def __init__(self, name=None):
        self.name = name
        self.state = State()

    @classmethod
    def create(cls, prev_name=None):
        game = cls()
        game.state.reset()
        success = False
        while not success:
            game.name = rand_chars(5)
            success = game.state.store(game.name, initial=True)

        if prev_name:
            async.link(prev_name, [game.name])
        return game

    def link(self, next_name):
        self.state.next_name = next_name
        self.state.step += 1
        self.log('link', next_name)

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

        async.peel(self.name, delay=1)

        if 'BOT' in self.state.nonces:
            async.loop_bot(self.name)

        return {}

    def peel(self):
        self.state.table += self.state.bag[0]
        self.state.bag = self.state.bag[1:]
        self.state.step += 1

        if len(self.state.bag) == 0:
            self.state.phase = PHASE_ENDGAME
            self.state.start_ts = time.time()
            self.log('endgame')
            # calling this now is guaranteed to not actually end
            self.end()
        else:
            async.peel(self.name, delay=settings.PEEL_DELAY)

        return None

    def end(self):
        delayed_time = time.time() - self.state.start_ts
        if delayed_time < settings.ENDGAME_TIME:
            # fix a tiny race condition, repeatedly try to end
            # the game until it is.
            async.end(self.name, delay=1)
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
            h for h, l in settings.BOTS.items()
            if l[0] == level
        ][0]

        self.join(handle, nonce='BOT')

        return {}

    def loop_bot(self):
        if self.state.phase == PHASE_ENDED:
            return {}

        player_num = self.state.nonces['BOT']
        handle = self.state.players[player_num][0]
        level, list_id, loop_ttl, max_word_len, comb_order = (
            settings.BOTS[handle]
        )

        if self.state.phase in (PHASE_STARTED, PHASE_ENDGAME):
            target, how = [easy_anagram, anagram][list_id].bot(
                self.state.table,
                sum([
                    words for _, words in self.state.players
                ], []),
                max_word_len,
                comb_order,
            )

            if target:
                self.play('BOT', target, how)

        async.loop_bot(self.name, delay=loop_ttl)
        return {}

    @classmethod
    def execute(cls, job):
        action = job.data['action']
        args = job.data.get('args', [])

        if action == 'create':
            game = cls.create(*args)
            result = {'name': game.name}
            job.write_result(result)
            return result

        name = job.data['name']
        game = cls(name)

        try:
            has_lock = False
            has_lock = fabric.acquire('lock:' + game.name)
            if not has_lock:
                job.retry()
                return

            start_step = end_step = None
            try:
                if not game.state.load(game.name):
                    raise GameError('Game not found.')
                start_step = game.state.step
                result = getattr(game, action)(*args)
                end_step = game.state.step
            except GameError, e:
                result = {'error': str(e)}
            except Exception, e:
                import traceback
                sys.stderr.write(traceback.format_exc() + '\n')
                result = {'error': str(e)}

            if result is not None:
                job.write_result(result)

            game.state.store(game.name)
            if start_step != end_step:
                fabric.notify(
                    'channel:' + game.name,
                    json.dumps(game.state.cleaned()),
                )

        finally:
            if has_lock:
                fabric.release('lock:' + game.name)

        return result

    def log(self, *message):
        self.state.log = self.state.log[-4:] + [
            (self.state.step,) + tuple(message),
        ]
