import json
import re
import settings


class Definitions(object):
    def __init__(self, filename):
        self.data = {}
        with open(filename, 'r') as fh:
            for line in fh:
                if not line.startswith('['):
                    continue
                try:
                    word, root, pos, sense, defn = json.loads(
                        line.strip().strip(','),
                    )
                except:
                    print line
                    raise
                if sense != 1:
                    continue
                defn = re.sub(r'{mdash}', '-', defn)
                if defn.startswith('< '):
                    defn = '<' + defn.split(' ')[1]
                self.data[word] = defn

    def lookup(self, word):
        defn = self.data.get(word)

        if not defn:
            return 'Definition not found.'

        if defn.startswith('<'):
            return self.data.get(
                defn[1:],
                'Missing defintion reference.',
            )

        if ' ' not in defn and defn.upper() in self.data:
            return defn.lower() + '; ' + self.data[defn.upper()]

        return defn


definitions = Definitions(settings.DEF_FILE_NASPA)


if __name__ == '__main__':
    print definitions.lookup('HELLO')
    print definitions.lookup('GORSE')
    print definitions.lookup('ZOWEE')
    print definitions.lookup('USELESSNESS')
