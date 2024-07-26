import logging
from logging.config import dictConfig
import os

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')

WORD_LIST = os.path.join(BASE_DIR, 'data/nwl2023.txt')
EASY_LIST = os.path.join(BASE_DIR, 'data/easy.txt')
DEF_FILE = os.path.join(BASE_DIR, 'data/def.txt')

# This file is not included in repo
DEF_FILE_NASPA = os.path.join(BASE_DIR, 'data/nwl2018-defs.json')

QUICK_LETTERS = (
    'AAAAABBCCDDEEEEEEEEFFGGHHIIIIIJKL'
    'LMMNNNOOOOPPQRRRRSSSTTTTUUVVWXYYZ'
)

LETTERS = (
    'AAAAAAAABBCCCDDDDEEEEEEEEEEEEFFGGGHHHIIIIIIIIJKKLL'
    'LLMMNNNNNNOOOOOOOOPPPQRRRRRRSSSSTTTTTTUUUUVVWWXYYZ'
)

SLOW_LETTERS = (
    'AAAAAAAAAAAABBBCCCDDDDDDEEEEEEEEEEEEEEEEEE'
    'FFFGGGGHHHIIIIIIIIIIIIJJKKLLLLLMMMNNNNNNNN'
    'OOOOOOOOOOOOPPPQQRRRRRRRRRSSSSSSTTTTTTTTTU'
    'UUUUUVVVWWWXXYYYZZ'
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

GAME_LENGTHS = {
    # (letters, peel_delay, endgame_time)
    1: (QUICK_LETTERS, 5.1, 60),
    2: (LETTERS, 5.7, 90),
    3: (SLOW_LETTERS, 5.9, 120),
}

DEBUG = True

BOTS = {
    # name: (level, list_id, loop_ttl, max_word_len, comb_order)
    'EasyBot': (0, 0, 31, 4, [0]),
    'OkayBot': (1, 0, 23, 6, [1, 0]),
    'HardBot': (2, 0, 19, 8, [1, 0]),
    'InsaneBot': (3, 1, 19, 8, [1, 0, 2]),
    'DeathBot': (4, 1, 15, 15, [1, 0, 2, 3]),
}

dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'game': {
            'format': '%(asctime)s\t%(message)s'
        }
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
        'game': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'game',
            'filename': '/var/log/snatch/game.log',
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
        'game': {
            'handlers': ['game'],
            'level': 'INFO',
            'propagate': False,
        },
    }
})
