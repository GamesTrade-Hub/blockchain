import time
import json
import hashlib
import logging
import requests
import sys

sys.path.append('../../')
sys.path.append('../')
from src.blockchain.keys import PrivateKey

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.setLevel(logging.DEBUG)


def get_time() -> int:
    return time.time_ns()


class BcEncoder(json.JSONEncoder):
    def default(self, o):
        # print("start", o)
        # print(o.__dict__)
        # for i in o.__dict__:
        #     print(':', i, o.__dict__[i])
        #     if o.__dict__[i].__class__.__module__ != 'builtins':
        #         print("no builtin result", o.__dict__[i].__class__.__module__,  json.dumps(o.__dict__[i], cls=BcEncoder))
        return {
            i: (
                o.__dict__[i].__str__()
                if o.__dict__[i].__class__.__module__ != "__builtin__"
                else o.__dict__[i]
            )
            for i in o.__dict__
        }


class MetaSingleton(type):
    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in MetaSingleton.__instances:
            print(f"Creating instance of {cls}")
            MetaSingleton.__instances[cls] = super(MetaSingleton, cls).__call__(
                *args, **kwargs
            )
        # print(MetaSingleton.__instances)
        return MetaSingleton.__instances[cls]


def hash__(data):
    return hashlib.sha256(data.encode()).hexdigest()


def post(rq, json_=None, headers=None, data=None):
    try:
        logger.info(f"-> POST {rq}")
        response = requests.post(rq, json=json_, headers=headers, data=data, timeout=4)
        logger.info(f"Response {response} received to {rq}")
        return response
    except ConnectionRefusedError as e:
        logger.error(f"[ConnectionRefusedError] Connection to {rq} refused {e}")
    except requests.exceptions.Timeout as e:
        logger.error(f"[Timeout] Timeout error on {rq} : {e}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[ConnectionError] Connection to {rq} failed {e}")
    except BaseException as e:
        logger.error(f"[ConnectionError] Connection to {rq} failed {e}")
    return None


def get(rq, json_=None, headers=None, data=None):
    try:
        logger.info(f"-> GET {rq}")
        response = requests.get(rq, json=json_, headers=headers, data=data, timeout=4)
        logger.info(f"Response {response} received to {rq}")
        return response
    except ConnectionRefusedError as e:
        logger.error(f"[ConnectionRefusedError] Connection to {rq} refused {e}")
    except requests.exceptions.Timeout as e:
        logger.error(f"[Timeout] Timeout error on {rq} : {e}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[ConnectionError] Connection to {rq} failed {e}")
    except BaseException as e:
        logger.error(f"[ConnectionError] Connection to {rq} failed {e}")
    return None
