import random
import requests
import time


BASE_URL = 'https://qa.snatch.cc/api/game'


while True:
    r = requests.post(BASE_URL)
    if r.status_code != 200:
        print 'BASE\n', r.content

    name = r.json()['name']
    print 'STARTING:', name
    handle = 'Jay'
    r = requests.post(BASE_URL + '/' + name + '/join', json={'handle': handle})
    if r.status_code != 200:
        print 'JOIN\n', r.content
    nonce = r.json()['nonce']

    r = requests.post(BASE_URL + '/' + name + '/options', json={'nonce': nonce, 'bot_level': 5})
    if r.status_code != 200:
        print 'OPTIONS\n', nonce, r.content

    r = requests.post(BASE_URL + '/' + name + '/start', json={'nonce': nonce})
    if r.status_code != 200:
        print 'START\n', r.content
