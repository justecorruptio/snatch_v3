import json
import time

from fabric import fabric, Job
import settings


PHASE_LOBBY = 1
PHASE_STARTED = 2
PHASE_ENDGAME = 3
PHASE_ENDED = 4

''' **** SCHEMA ****
    phase: phase number
    step: vector clock
    start_ts: start_ts of this phase
    bag: list of letters
    table: string of letters
    log: list of log messages, recent last
    players: list of players
    nonces: dict mapping nonce key to player number
    next_name: name of the next game.

    **** PLAYER ****
    handle: name
    words: list of words
'''


class State(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def reset(self):
        self.update(
            phase=PHASE_LOBBY,
            step=0,
            start_ts=time.time(),
            bag='',
            table='',
            log=[],
            players=[],
            nonces={},
            next_name=None,
        )
        if 'options' not in self:
            self['options'] = {
                'bot_level': 0,
                'min_word': 3,
                'game_length': 2,
                'ruleset': 1,
            }

    def add_player(self, handle):
        self.players.append({
            'handle': handle,
            'words': [],
            'end_vote': False,
        })

    def end_votes(self):
        voted = 0
        total = 0
        for nonce, player_id in self.nonces.iteritems():
            if nonce == 'BOT':
                continue
            total += 1
            if self.players[player_id]['end_vote']:
                voted += 1
        return [voted, total]

    def cleaned(self):
        ret = dict(self)
        if 'nonces' in ret:
            if 'BOT' in ret['nonces']:
                ret['has_bot'] = True
            ret.pop('nonces')
        if 'bag' in ret:
            ret['bag'] = len(ret['bag'])
        if 'start_ts' in ret:
            game_length = self.options['game_length']
            endgame_time = settings.GAME_LENGTHS[game_length][2]
            ret['time_left'] = (
                endgame_time - (time.time() - ret['start_ts'])
            )

        ret['end_votes'] = self.end_votes()

        return ret

    def store(self, key, initial=False):
        return fabric.store(
            'game:' + key,
            json.dumps(self),
            nx=initial,
            ex=settings.GAME_TTL,
        )

    def load(self, key):
        serialized = fabric.load('game:' + key)
        if serialized is None:
            return False
        self.update(**json.loads(serialized))
        return True

    def __str__(self):
        return json.dumps(self)
