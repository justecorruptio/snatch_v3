import json
import logging
import random
import sys
import time

from anagram import anagram, easy_anagram
from definitions_naspa import definitions
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
from utils import make_bag, rand_chars, lru


class GameError(Exception):
    pass


class Game(object):

    logger = logging.getLogger('daemon')
    game_logger = logging.getLogger('game')

    def __init__(self, name=None):
        self.name = name
        self.state = State()

    @classmethod
    def create(cls, prev_name=None):
        game = cls()
        if prev_name is not None:
            game.state.load(prev_name)
        game.state.reset()
        success = False
        while not success:
            game.name = rand_chars(5)
            success = game.state.store(game.name, initial=True)

        if prev_name:
            async.link(prev_name, [game.name])

        bot_level = game.state.options['bot_level']
        if bot_level > 0:
            async.add_bot(game.name, [bot_level])

        return game

    def link(self, next_name):
        self.state.next_name = next_name
        self.state.step += 1
        self.log('link', next_name)

    def join(self, handle, nonce=None):
        while self.state.next_name is not None:
            self.name = self.state.next_name
            self.state = State()
            self.state.load(self.name)

        if any(p['handle'] == handle for p in self.state.players):
            return {'error': 'duplicate name'}
        next_player_num = len(self.state.players)
        if nonce is None:
            nonce = '%s_%03d' % (rand_chars(7), next_player_num)
        self.state.add_player(handle)
        self.state.nonces[nonce] = next_player_num

        self.state.step += 1
        self.log('join', handle)

        return {'nonce': nonce, 'name': self.name}

    def leave(self, nonce):
        player_num = self.state.nonces.get(nonce, None)
        if player_num is None:
            return {'error': 'invalid player'}

        handle = self.state.players[player_num]['handle']
        del self.state.players[player_num]
        for key, val in self.state.nonces.items():
            if val > player_num:
                self.state.nonces[key] -= 1
        del self.state.nonces[nonce]

        self.state.step += 1
        self.log('leave', handle)

        return {}

    def start(self, nonce):

        player_num = self.state.nonces.get(nonce, None)
        if player_num is None:
            return {'error': 'invalid player'}

        if self.state.phase != PHASE_LOBBY:
            return {'error': 'invalid state'}

        self.state.phase = PHASE_STARTED
        self.state.start_ts = time.time()
        game_length = self.state.options['game_length']
        letters = settings.GAME_LENGTHS[game_length][0]
        self.state.bag = make_bag(letters)
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
            game_length = self.state.options['game_length']
            peel_delay = settings.GAME_LENGTHS[game_length][1]
            table_length = len(self.state.table)
            if table_length < 12:
                multiplier = 1.0
            elif table_length < 24:
                multiplier = 1.5
            elif table_length < 40:
                multiplier = 2.3
            else:
                multiplier = 3.7
            async.peel(self.name, delay=peel_delay * multiplier)

        return None

    def end(self):
        delayed_time = time.time() - self.state.start_ts
        game_length = self.state.options['game_length']
        endgame_time = settings.GAME_LENGTHS[game_length][2]
        end_voted, end_total = self.state.end_votes()
        if delayed_time < endgame_time and not end_voted == end_total:
            # fix a tiny race condition, repeatedly try to end
            # the game until it is.
            async.end(self.name, delay=1)
            return

        self.state.phase = PHASE_ENDED
        self.state.start_ts = time.time()
        self.state.step += 1
        self.log('end')

        self.game_logger.info(str(self.state))

        return None

    def play(self, nonce, target, how=None):
        player_num = self.state.nonces.get(nonce, None)
        if player_num is None:
            return {'error': 'Invalid player'}

        if len(target) < self.state.options['min_word']:
            return {'error': 'Minimum word length is %s' % (
                self.state.options['min_word'],
            )}

        if not anagram.is_word(target):
            return {'error': '%s is not a word' % (target,)}

        if how is None:
            how, error = anagram.check(
                self.state.table,
                sum([player['words'] for player in self.state.players], []),
                target,
                rearrange=self.state.options['ruleset'] == 2,
            )

        if how is None:
            return {'error': error}

        status = None
        for w in how:
            for i, player in enumerate(self.state.players):
                words = player['words']
                if w in words:
                    words.remove(w)
                    status = ('steal', target, player_num, w, i)
                    break
            # table and player words are mutually exclusive.
            if len(w) == 1 and w in self.state.table:
                table = list(self.state.table)
                table.remove(w)
                self.state.table = ''.join(table)

        if not status:
            status = ('play', target, player_num)

        self.state.players[player_num]['words'].append(target)
        self.state.step += 1

        self.log(*status)

        if self.state.phase == PHASE_ENDGAME:
            self.state.start_ts = time.time()

        return {}

    def set_options(self, nonce, bot_level=None, min_word=None, game_length=None, ruleset=None):

        if self.state.phase != PHASE_LOBBY:
            return {'error': 'invalid state'}

        player_num = self.state.nonces.get(nonce, None)
        if player_num is None:
            return {'error': 'invalid player'}

        if bot_level is not None:
            self.state.options['bot_level'] = bot_level
            if bot_level > 0:
                return self.add_bot(bot_level)
            else:
                return self.remove_bot()

        if min_word is not None:
            self.state.options['min_word'] = min_word
            self.state.step += 1

        if game_length is not None:
            self.state.options['game_length'] = game_length
            self.state.step += 1

        if ruleset is not None:
            self.state.options['ruleset'] = ruleset
            self.state.step += 1

        return {}

    def end_now(self, nonce):
        player_num = self.state.nonces.get(nonce, None)
        if player_num is None:
            return {'error': 'Invalid player'}

        self.state.players[player_num]['end_vote'] = True
        self.state.step += 1

        return {}

    def add_bot(self, level):

        self.remove_bot()

        handle = [
            h for h, l in settings.BOTS.items()
            if l[0] == level - 1
        ][0]

        self.join(handle, nonce='BOT')

        return {}

    def remove_bot(self):
        if 'BOT' not in self.state.nonces:
            return {}

        self.leave('BOT')

        return {}

    def loop_bot(self):
        if self.state.phase == PHASE_ENDED:
            return {}

        player_num = self.state.nonces['BOT']
        handle = self.state.players[player_num]['handle']
        level, list_id, loop_ttl, max_word_len, comb_order = (
            settings.BOTS[handle]
        )
        min_word_len = self.state.options['min_word']

        if self.state.phase in (PHASE_STARTED, PHASE_ENDGAME):
            target, how = [easy_anagram, anagram][list_id].bot(
                self.state.table,
                sum([
                    player['words'] for player in self.state.players
                ], []),
                min_word_len,
                max(min_word_len, max_word_len),
                comb_order,
                rearrange=self.state.options['ruleset'] == 2,
            )

            if target:
                self.play('BOT', target, how)

        async.loop_bot(self.name, delay=loop_ttl)
        return {}

    @classmethod
    @lru(100)
    def word_info(cls, word):
        return {
            'definition': definitions.lookup(word),
            'extensions': anagram.extensions(word),
        }

    @classmethod
    def execute(cls, job):
        action = job.data['action']
        args = job.data.get('args', [])

        if action == 'create':
            game = cls.create(*args)
            result = {'name': game.name}
            job.write_result(result)
            return result

        if action == 'word_info':
            result = cls.word_info(*args)
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
                game.state.store(game.name)
            except GameError, e:
                result = {'error': str(e)}
            except Exception, e:
                import traceback
                cls.logger.error('DATA: ' + str(job.data))
                cls.logger.error(traceback.format_exc())
                result = {'error': str(e)}

            if result is not None:
                job.write_result(result)

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
        self.state.log = self.state.log[-6:] + [
            (self.state.step,) + tuple(message),
        ]
