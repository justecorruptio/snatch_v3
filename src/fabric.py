import json
from redis import StrictRedis
import time

import settings
from utils import rand_chars

ZPOP = """
    local zkey = ARGV[1]
    local now_ts = ARGV[2]

    local zhead = redis.call('ZRANGE', zkey, 0, 0, 'WITHSCORES')
    if zhead[1] ~= nil and tonumber(zhead[2]) <= tonumber(now_ts) then
        redis.call('ZREM', zkey, zhead[1])
        return zhead
    end

    return nil
"""

BACKOFF_PLAN = ([0] * 5 + [1] * 20 + [2])

redis = StrictRedis(**settings.REDIS)
redis.zpop = redis.register_script(ZPOP)


class FabricException(Exception):
    pass


class Job(object):

    def __init__(self, **data):
        self.data = data
        self.result_key = None
        self.fabric_key = None

    def retry(self, delay=.01):
        fabric.defer_job(self.fabric_key, self, delay=delay)

    def write_result(self, result):
        if self.result_key is None:
            raise FabricException('Result written by client')
        pipeline = redis.pipeline()
        pipeline.rpush(self.result_key, json.dumps(result))
        pipeline.expire(self.result_key, settings.RESULT_TTL)
        pipeline.execute()

    @property
    def result(self):
        if self.result_key is None:
            raise FabricException('Job not sent')
        return json.loads(redis.blpop(self.result_key)[1])

    @property
    def result_json(self):
        if self.result_key is None:
            raise FabricException('Job not sent')
        return redis.blpop(self.result_key)[1]


class Fabric(object):
    """Singleton?"""

    def poll(self, key):
        """returns a tuple of message and planned time."""
        tries = 0
        backoff_ms = 0
        while True:
            now_ms = int(time.time() * 1000)
            res = redis.zpop(args=[key, now_ms + backoff_ms])

            if res is not None:
                mesg, planned_ms = res
                return mesg, int(planned_ms) / 1000.

            if tries < len(BACKOFF_PLAN):
                backoff_ms = BACKOFF_PLAN[tries]
            else:
                backoff_ms = BACKOFF_PLAN[-1]
            time.sleep(backoff_ms / 1000.)
            tries += 1

    def defer(self, key, message, delay=0):
        """delay in seconds"""

        eta = int((time.time() + delay) * 1000)
        redis.zadd(key, eta, message)


    def poll_job(self, key):
        message, planned_ts = self.poll(key)
        data, result_key = json.loads(message)
        job = Job(**data)
        job.result_key = result_key
        job.fabric_key = key
        job.planned_ts = planned_ts
        return job

    def defer_job(self, key, job, delay=0):
        if job.result_key is None:
            job.result_key = 'result:' + rand_chars(16)

        message = json.dumps((job.data, job.result_key))
        return self.defer(key, message, delay=delay)

    def store(self, key, data, **kwargs):
        return redis.set(key, data, **kwargs)

    def load(self, key):
        return redis.get(key)

    def acquire(self, key):
        return redis.set(key, '1', nx=True, ex=settings.LOCK_TTL)

    def release(self, key):
        redis.delete(key)

    def wait(self, key, timeout=60 * 10):
        pubsub = redis.pubsub()
        pubsub.subscribe(key)

        start_ts = time.time()
        try:
            while True:
                res = pubsub.parse_response(block=False, timeout=.1)
                now = time.time()

                if now - start_ts > timeout:
                    return None

                if res is None:
                    continue

                msg_type, channel, message = res
                if msg_type == 'message':
                    return message
        finally:
            pubsub.close()

    def notify(self, key, message):
        redis.publish(key, message)

fabric = Fabric()

if __name__ == '__main__':
    f = fabric

    '''
    a = Job(name='second')
    f.defer_job('A', a, delay=2.5)
    b = Job(name='first')
    f.defer_job('A', b, delay=1)

    job = f.poll_job('A')
    job.retry(delay=2)

    for i in xrange(2):
        job = f.poll_job('A')
        job.write_result('RAN %s %s' % (
            job.data['name'],
            time.time(),
        ))

    print b.result
    print a.result
    '''
