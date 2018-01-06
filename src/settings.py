import logging
from logging.config import dictConfig
import os

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')

WORD_LIST = os.path.join(BASE_DIR, 'data/twl.txt')
EASY_LIST = os.path.join(BASE_DIR, 'data/easy.txt')

SCRABBLE_LETTERS = (
    'AAAAAAAAABBCCDDDDEEEEEEEEEEEEFFGGGHHIIIIIIIIIJKLL'
    'LLMMNNNNNNOOOOOOOOPPQRRRRRRSSSSTTTTTTUUUUVVWWXYYZ'
)

QUICK_LETTERS = (
    'AAAAABBCCDDEEEEEEEEFFGGHHIIIIIJKL'
    'LMMNNNOOOOPPQRRRRSSSTTTTUUVVWXYYZ'
)

LETTERS = (
    'AAAAAAAABBCCCDDDDEEEEEEEEEEEEFFGGGHHHIIIIIIIIJKKLL'
    'LLMMNNNNNNOOOOOOOOPPPQRRRRRRSSSSTTTTTTUUUUVVWWXYYZ'
)

REDIS = dict(
    host='localhost',
    port=6379,
    db=0,
)

GAME_TTL = 60 * 60
LOCK_TTL = 5
RESULT_TTL = 10

QUEUE_NAME = 'snatchq'
PEEL_DELAY = 5.1
#PEEL_DELAY = .1
ENDGAME_TIME = 60
#ENDGAME_TIME = 10

DEBUG = True

BOTS = {
    # name: (level, list_id, loop_ttl, max_word_len, comb_order)
    'EasyBot': (0, 0, 47, 5, [0]),
    'OkayBot': (1, 0, 37, 6, [0, 1]),
    'HardBot': (2, 1, 27, 8, [1, 0]),
    'InsaneBot': (3, 1, 16, 10, [1, 0, 2]),
    'DeathBot': (4, 1, 3.3, 15, [1, 0, 2, 3]),
}

dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'daemon': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'default',
            'filename': '/var/log/snatch/daemon.log',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 1000,
        },
        'api': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'default',
            'filename': '/var/log/snatch/api.log',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 1000,
        },
    },
    'loggers': {
        'daemon': {
            'handlers': ['daemon'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'api': {
            'handlers': ['api'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
})
