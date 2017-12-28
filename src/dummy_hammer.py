import random
import requests
import time


BASE_URL = 'http://localhost:8080/game'

while True:

    r = requests.post(BASE_URL)
    name = r.json()['name']

    requests.post(BASE_URL + '/' + name + '/start')

    #time.sleep(random.random() / 100)

