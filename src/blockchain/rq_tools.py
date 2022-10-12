import logging
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.setLevel(logging.DEBUG)


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
