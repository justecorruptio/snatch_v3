import json

from fabric import fabric, Job
import settings

class Service(object):

    def __init__(self, wait=True):
        self.wait = wait

    def __getattr__(self, action):
        def wrapped(name, args=None, delay=0, as_json=False):
            if args is None:
                args = []
            job = Job(action=action, name=name, args=args)
            fabric.defer_job(
                settings.QUEUE_NAME,
                job,
                delay=delay,
            )
            if self.wait:
                if as_json:
                    return job.result_json
                else:
                    return job.result
            else:
                return None
        return wrapped


sync = Service(wait=True)
async = Service(wait=False)
