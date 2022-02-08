import time
import json
import hashlib


def get_time():
    return time.time_ns()


class BcEncoder(json.JSONEncoder):
    def default(self, o):
        # print("start", o)
        # print(o.__dict__)
        # for i in o.__dict__:
        #     print(':', i, o.__dict__[i])
        #     if o.__dict__[i].__class__.__module__ != 'builtins':
        #         print("no builtin result", o.__dict__[i].__class__.__module__,  json.dumps(o.__dict__[i], cls=BcEncoder))
        return {i: (o.__dict__[i].__str__() if o.__dict__[i].__class__.__module__ != '__builtin__' else o.__dict__[i]) for i in o.__dict__}


class MetaSingleton(type):
    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in MetaSingleton.__instances:
            print(f'Creating instance of {cls}')
            MetaSingleton.__instances[cls] = super(MetaSingleton, cls).__call__(*args, **kwargs)
        print(MetaSingleton.__instances)
        return MetaSingleton.__instances[cls]


def hash(data):
    return hashlib.sha256(data.encode()).hexdigest()


