import random
import requests
import time


BASE_URL = 'http://localhost/snatch_api/game'


while True:
    r = requests.post(BASE_URL)
    name = r.json()['name']
    handle = 'Jay'
    r = requests.post(BASE_URL + '/' + name + '/join', json={'handle': handle})
    nonce = r.json()['nonce']

    r = requests.post(BASE_URL + '/' + name + '/addBot', json={'nonce': nonce, 'level': 5})

    requests.post(BASE_URL + '/' + name + '/start', json={'nonce': nonce})

    time.sleep(.1)
