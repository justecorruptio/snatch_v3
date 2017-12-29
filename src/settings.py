import os

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')

WORD_LIST = os.path.join(BASE_DIR, 'data/twl.txt')

SCRABBLE_LETTERS = (
    'AAAAAAAAABBCCDDDDEEEEEEEEEEEEFFGGGHHIIIIIIIIIJKLL'
    'LLMMNNNNNNOOOOOOOOPPQRRRRRRSSSSTTTTTTUUUUVVWWXYYZ'
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
#PEEL_DELAY = 0
MIN_WORD_LENGTH = 4
ENDGAME_TIME = 60
#ENDGAME_TIME = 1

DEBUG = True
