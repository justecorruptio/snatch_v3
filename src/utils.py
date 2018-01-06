import random

from string import ascii_uppercase


def rand_chars(length):
    return ''.join(
        random.choice(ascii_uppercase)
        for i in xrange(length)
    )


def is_int_in_range(val, low, high):
    # inclusive, None is ok
    if val is None:
        return True
    if not isinstance(val, int):
        return False
    return val >= low and val <= high


def near_merge(a, b):
    if not a:
        return b
    if not b:
        return a

    la = len(a) + 1
    lb = len(b) + 1

    pa = random.randint(int(la * .4), int(la * .6))
    pb = random.randint(int(lb * .4), int(lb * .6))

    return (
        near_merge(a[:pa], b[:pb]) +
        near_merge(a[pa:], b[pb:])
    )


def make_bag(letters):
    vowels = [c for c in letters if c in 'AEIOU']
    conson = [c for c in letters if c not in 'AEIOU']
    random.shuffle(vowels)
    random.shuffle(conson)
    return ''.join(near_merge(vowels, conson))

