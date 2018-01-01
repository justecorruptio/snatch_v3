import json
import time

from fabric import fabric, Job
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

    def reset(self):
        self.update(
            phase=PHASE_LOBBY,
            step=0,
            start_ts=time.time(),
            bag=settings.LETTERS,
            table='',
            log=[],
            players=[],
            nonces={},
            next_name=None,
        )

    def cleaned(self):
        ret = dict(self)
        if 'nonces' in ret:
            if 'BOT' in ret['nonces']:
                ret['has_bot'] = True
            ret.pop('nonces')
        if 'bag' in ret:
            ret['bag'] = len(ret['bag'])
        if 'start_ts' in ret:
            ret['time_left'] = (
                settings.ENDGAME_TIME -
                (time.time() - ret['start_ts'])
            )
        return ret

    def store(self, key, initial=False):
        return fabric.store(
            key,
            json.dumps(self),
            nx=initial,
            ex=settings.GAME_TTL,
        )

    def load(self, key):
        serialized = fabric.load(key)
        if serialized is None:
            return False
        self.update(**json.loads(serialized))
        return True
