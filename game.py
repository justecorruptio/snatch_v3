import redis

import settings

class Game(object):

    STATE_LOBBY = 10
    STATE_STARTED = 20
    STATE_ENDGAME = 30
    STATE_ENDED = 40

    def __init__(self):
        self.state = self.STATE_LOBBY
        self.bag = settings.SCRABBLE_LETTERS
