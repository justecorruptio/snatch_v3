from itertools import combinations

LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
PRIMES = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41,
    43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101
]
LETTERS_TO_PRIMES = dict(zip(LETTERS, PRIMES))

class Anagram(object):

    def __init__(self):
        self.data = {}
        self.tiered = [{} for i in xrange(16)]

        fh = open('twl.txt', 'r')
        for line in fh:
            line = line.strip()
            hx = self.hash(line)
            self.data.setdefault(hx, []).append(line)
            self.tiered[len(line)].setdefault(hx, []).append(line)

    def hash(self, letters):
        global LETTERS_TO_PRIMES
        r = 1
        for c in letters:
            r *= LETTERS_TO_PRIMES[c]
        return r

    def lookup(self, letters):
        return self.data.get(self.hash(letters), [])

    def snatch(self, words):
        res = set()
        letters = [w for w in words if len(w) == 1]
        words = [w for w in words if len(w) > 1]

        letter_hashes = [
            [(l, self.hash(l)) for l in combinations(letters, j)]
            for j in xrange(min(len(letters) + 1, 15))
        ]

        for i in xrange(min(len(words) + 1, 4)):
            for w in combinations(words, i):
                combo = ''.join(w)
                if len(combo) > 15:
                    continue
                words_hx = self.hash(combo)

                for entries in letter_hashes[max(0, 2 - len(w)):15 - len(combo)]:
                    for l, letter_hx in entries:
                        hx = words_hx * letter_hx
                        if hx not in self.data:
                            continue
                        for built in self.data[hx]:
                            res.add((tuple(sorted(w) + sorted(l)), built))

        res = list(res)
        res.sort(key=lambda r: (len(r[1]), r[0]))
        return res

    def extend(self, word):
        res = set()
        ix = self.hash(word)
        for i in xrange(len(word), 15):
            for hx, builts in self.tiered[i].iteritems():
                if hx >= ix and hx % ix == 0:
                    for built in builts:
                        sub = self.subtract(built, word)
                        res.add((tuple([word] + sorted(sub)), built))

        res = list(res)
        res.sort(key=lambda r: (len(r[1]), r[0]))
        return res

    def subtract(self, a, b):
        a = list(a)
        for c in b:
            a.remove(c)
        return tuple(a)

def main():
    import time
    a = time.time()
    anagram = Anagram()
    print time.time() - a

    a = time.time()
    res = anagram.snatch("""
        adjunct professor anomally detection
        machine learning splitting heading
        proclaim announce jinx hybrid
        dexter corpse anneal index
        marbling dietary genious
        dubious apple tides marches
        petered daffodill hungry
        q r g k i o
    """.upper().strip().split())
    for combo, built in res:
        print ' + '.join(combo), '=', built
    print time.time() - a

    '''
    a = time.time()
    res = anagram.extend('TEACH')
    for combo, built in res:
        print ' + '.join(combo), '=', built
    print time.time() - a
    '''

if __name__ == '__main__':
    main()
