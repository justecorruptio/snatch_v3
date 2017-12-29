from itertools import combinations
import random

import settings


LETTERS = 'ETAOINSHRDLUFCMGYPWBVKXJQZ'
PRIMES = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41,
    43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101
]
LETTERS_TO_PRIMES = dict(zip(LETTERS, PRIMES))

def product(arr):
    r = 1
    for x in arr:
        r *= x
    return r


class Anagram(object):

    def __init__(self):
        self.data = {}

        fh = open(settings.WORD_LIST, 'r')
        for line in fh:
            line = line.strip()
            hx = self.hash(line)
            self.data.setdefault(hx, []).append(line)
        fh.close()


    def hash(self, letters):
        global LETTERS_TO_PRIMES
        r = 1
        for c in letters:
            r *= LETTERS_TO_PRIMES[c]
        return r

    def subtract(self, big, *smalls):
        big = list(big)
        for small in smalls:
            for c in small:
                big.remove(c)
        return big

    def check(self, table, all_words, target):

        target_hx = self.hash(target)
        table_hx = self.hash(table)

        word_hashes = []
        for w in all_words:
            hx = self.hash(w)
            if target_hx % hx == 0:
                word_hashes.append((w, hx))

        error = '%s is not on the board.' % (target,)
        for i in xrange(5):
            for comb in combinations(word_hashes, i):
                p = product([hx for w, hx in comb])
                d, m = divmod(target_hx, p)

                # disallow just plain stealing
                if len(comb) == 1 and d == 1:
                    error = 'You must add letters.'
                    continue

                if m == 0 and table_hx % d == 0:
                    words = [w for w, hx in comb]
                    return words + self.subtract(target, *words), None

        return None, error

    def bot(self, table, words, max_word_len):

        # protect ourselves from segfault
        table = table[-10:]

        letter_hashes = [None] * 16

        for i in xrange(4, -1, -1):
            for w in combinations(words, i):
                combo = ''.join(w)
                if len(combo) > max_word_len:
                    continue
                words_hx = self.hash(combo)

                for j in xrange(
                    [4, 1, 0, 0, 0][i],
                    max_word_len - len(combo) + 1,
                    1,
                ):
                    if letter_hashes[j] is None:
                        letter_hashes[j] = [
                            (l, self.hash(l))
                            for l in combinations(table, j)
                        ]
                    entries = letter_hashes[j]
                    for l, letter_hx in entries:
                        hx = words_hx * letter_hx
                        if hx not in self.data:
                            continue

                        return (
                            random.choice(self.data[hx]),
                            list(w) + list (l),
                        )
        return None, None

    def is_word(self, target):
        target_hx = self.hash(target)
        return target in self.data.get(target_hx, [])

anagram = Anagram()


if __name__ == '__main__':

    import time
    a = time.time()
    #res = anagram.check(list('TYBE'), ['VAIN', 'GAS'], 'VANITY')
    res = anagram.check('EMPSTH', ['HEED', 'BAD'], 'BEHEADED')
    b = time.time()
    print res, '%0.2f ms' % ((b - a) * 1000,)

    a = time.time()
    res = anagram.bot('EMPSTH', ['HEED', 'BAD'], 6)
    b = time.time()
    print res, '%0.2f ms' % ((b - a) * 1000,)
