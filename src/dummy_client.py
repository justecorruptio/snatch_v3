import requests
import sys
import threading


BASE_URL = 'https://qa.snatch.cc/api/game'

sys.argv.pop(0)

# TODO: real arg handling
if len(sys.argv) == 1:
    handle, name = sys.argv[0], None
elif len(sys.argv) == 2:
    handle, name = sys.argv

if name is None:
    r = requests.post(BASE_URL)
    name = r.json()['name']

    requests.post(BASE_URL + '/' + name + '/start')

r = requests.post(BASE_URL + '/' + name + '/join', json={'handle': handle})
nonce = r.json()['nonce']

step = None
phase = 0

sys.stdout.write('\033[2J')

def worker():
    global step
    url = BASE_URL + '/' + name
    if step is not None:
        url += '?step=' + str(step)
    r = requests.get(url)
    r = r.json()

    sys.stdout.write('\033[2J\033[H')
    print '===== GAME:', name, '======\n'
    print '     Table:', r['table'], '\n'

    for h, words in r['players']:
        print '%10s:' % (h,), ' '.join(words)

    step = r['step']
    phase = r['phase']
    if phase == 4:
        print "GAME OVER"
        sys.exit(0)

    sys.stdout.write('\nWord: ')
    sys.stdout.flush()

def display_loop():
    while True:
        worker()

thread = threading.Thread(target=display_loop)
thread.daemon = True
thread.start()

while True:
    word = raw_input().strip()
    r = requests.post(BASE_URL + '/' + name + '/play', json={'nonce': nonce, 'word': word})
    print r.json()
