from redis import StrictRedis
import time

import settings

ZPOP = """
    local zkey = ARGV[1]
    local now_ts = ARGV[2]

    local zhead = redis.call('ZRANGE', zkey, 0, 0, 'WITHSCORES')
    if zhead[1] ~= nil and tonumber(zhead[2]) <= tonumber(now_ts) then
        redis.call('ZREM', zkey, zhead[1])
        return zhead[1]
    end

    return nil
"""

BACKOFF_PLAN = [0, 1, 2, 5, 5, 10, 10, 20, 20, 20, 50]

class Fabric(object):

    redis = StrictRedis(**settings.REDIS)
    zpop = redis.register_script(ZPOP)

    def __init__(self):
        pass

    def poll(self, key):
        tries = 0
        while True:
            now_ms = int(time.time() * 1000)
            mesg = self.zpop(args=[key, now_ms])
            if mesg is not None:
                return mesg
            if tries < len(BACKOFF_PLAN):
                backoff_ms = BACKOFF_PLAN[tries]
            else:
                backoff_ms = BACKOFF_PLAN[-1]
            time.sleep(backoff_ms / 1000.)
            tries += 1

    def push(self, key, message, delay=0):
        """delay in seconds"""

        eta = int((time.time() + delay) * 1000)
        self.redis.zadd(key, eta, message)

    def store(self, key, data, **kwargs):
        return self.redis.set(key, data, **kwargs)

    def load(self, key):
        return self.redis.get(key)

if __name__ == '__main__':
    f = Fabric()
    f.push('A', 'first')
    f.push('A', 'third', delay=3)
    f.push('A', 'second', delay=2)

    for i in xrange(3):
        print f.poll('A')
