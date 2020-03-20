import re
import settings


class Definitions(object):
    def __init__(self, filename):
        self.data = {}
        with open(filename, 'r') as fh:
            for line in fh:
                line = line.strip()
                words, definition = line.split('\t', 1)
                match = re.search(
                    r'(?:[A-Z]+)[A-Z ]*[/a-z]+\s(?:pl\.\s)?(?:[-, A-Z]|or)*((?:[A-Z]?[-, a-z])*)',
                    definition,
                )
                if match:
                    definition = match.groups()[0]
                else:
                    definition = ''

                for word in words.split(' '):
                    self.data[word] = definition.strip()
                    #if not definition:
                    #    print word, definition

    def lookup(self, word):
        return self.data.get(
            word.lower(),
        ) or 'Definition not found.'


definitions = Definitions(settings.DEF_FILE)


if __name__ == '__main__':
    print definitions.lookup('hello')
