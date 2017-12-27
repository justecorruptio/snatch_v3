import random

from string import ascii_uppercase

def rand_chars(length):
    return ''.join(
        random.choice(ascii_uppercase)
        for i in xrange(length)
    )
