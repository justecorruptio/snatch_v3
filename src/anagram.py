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

    def __init__(self, word_list):
        self.data = {}

        fh = open(word_list, 'r')
        for line in fh:
            line = line.upper().strip()
            hx = self.hash(line)
            self.data.setdefault(hx, []).append(line)
        fh.close()

        self.ordered_hx = [[] for i in xrange(16)]
        for hx, words in sorted(self.data.iteritems()):
            self.ordered_hx[len(words[0])].append(hx)

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

    def check(self, table, all_words, target, rearrange=False):

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
                if i == 1:
                    if d == 1:
                        error = 'You must add letters.'
                        continue

                    if comb[0][0] + 'S' == target:
                        error = 'Plural, adding S is not allowed.'
                        continue

                if m == 0 and table_hx % d == 0:
                    words = [w for w, hx in comb]
                    sub = self.subtract(target, *words)
                    if (
                        rearrange and
                        i == 1 and
                        not self.is_rearranged(target, words[0], sub)
                    ):
                        error = 'Stolen word must be rearranged.'
                        continue
                    return words + sub, None

        return None, error

    def bot(self, table, words, min_word_len, max_word_len, comb_order, rearrange=False):

        # protect ourselves from segfault
        table = table[-10:]

        letter_hashes = [None] * 16

        for i in comb_order:
            for w in combinations(words, i):
                combo = ''.join(w)
                if len(combo) > max_word_len:
                    continue
                words_hx = self.hash(combo)

                for j in xrange(
                    max_word_len - len(combo),
                    [min_word_len, 1, 0, 0, 0][i] - 1,
                    -1,
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

                        target = random.choice(self.data[hx])

                        if i == 1:
                            if target == w[0] + 'S':
                                continue
                            if rearrange and not self.is_rearranged(target, w[0], l):
                                continue

                        return target, list(w) + list(l)
        return None, None

    def is_word(self, target):
        target_hx = self.hash(target)
        return target in self.data.get(target_hx, [])

    def is_rearranged(self, target, word, sub):
        sub = list(sub)
        word = list(word)
        for c in target:
            if not word:
                return False
            if c == word[0]:
                word = word[1:]
                continue
            if c in sub:
                sub.remove(c)
                continue
            return True
        return False

    def extensions(self, word):
        hx = self.hash(word)
        tmp = []
        for i in xrange(len(word) + 1, 16):
            for other in self.ordered_hx[i]:
                if other % hx == 0 and other != hx:
                    tmp.extend(self.data.get(other, []))
                    if len(tmp) > 50:
                        break
            if len(tmp) > 10:
                break
        tmp.sort(key=lambda x: (len(x), x))

        result = []
        for ext in tmp:
            res_word = ext
            for letter in self.subtract(ext, word):
                res_word = res_word.replace(letter, letter.lower(), 1)
            result.append(res_word)
        return result


anagram = Anagram(settings.WORD_LIST)
easy_anagram = Anagram(settings.EASY_LIST)


if __name__ == '__main__':

    import time
    a = time.time()
    #res = anagram.check(list('TYBE'), ['VAIN', 'GAS'], 'VANITY')
    res = anagram.check('EMPSTH', ['HEED', 'BAD'], 'BEHEADED')
    b = time.time()
    print res, '%0.2f ms' % ((b - a) * 1000,)

    a = time.time()
    res = anagram.bot('EMPSTH', ['HEED', 'BAD'], 6, 7, [1, 0])
    #res = anagram.bot('SAD', ['HEED'], 8, [1, 0])
    b = time.time()
    print res, '%0.2f ms' % ((b - a) * 1000,)

    print anagram.is_rearranged('HEALTH', 'EAT', 'HHL') # F
    print anagram.is_rearranged('HEALTH', 'ETA', 'HHL') # T
    print anagram.is_rearranged('ABC', 'AB', 'C') # F
    print anagram.is_rearranged('ABC', 'BC', 'A') # F
    print anagram.is_rearranged('ABC', 'B', 'AC') # F
    print anagram.is_rearranged('ABC', 'CA', 'B') # T

    print anagram.bot('O', ['HELL'], 3, 7, [1, 0], True) # non found

    print anagram.extensions('OUGUI')
    print anagram.extensions('MEDICARE')
