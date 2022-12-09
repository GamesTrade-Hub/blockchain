import logging
import requests
import uuid

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.setLevel(logging.DEBUG)


class ResponseCustom:
    def __init__(self, resp):
        self.status_code = resp["code"]
        self.text = str(resp["message"])
        self.json_ = resp["message"]
        self.reason = "J'ai pas envie de donner de raison, je suis sincèrement désolé d'avoir cette turbo flemme en moi"
        self.content = str(resp["message"])
        
    def json(self):
        return self.json_


def post(rq, json_=None, headers=None, data=None):
    from src.TCPServer.tmp_test_impl import tcp_client, tcp_server
    print("\n\n\n\n\nCECI EST LA REQUESTS POST ->", rq, tcp_server, tcp_client)
    try:
        print(rq.split('/', 3))
        path = "/" + rq.split('/', 3)[3]
        client_uuid = uuid.UUID(rq[7:43])
        if tcp_server is not None:
            client = tcp_server.clients_list.get_client_per_uuid(str(client_uuid))
            resp = client.post(route=path, json_obj=json_)
            print("ET LA REPONSE : ", resp, "\n\n\n\n\n")
            return ResponseCustom(resp)
        if tcp_client is not None:
            # client = tcp_client.client
            resp = tcp_client.post(route=path, json_obj=json_)
            print("ET LA REPONSE : ", resp, "\n\n\n\n\n")
            return ResponseCustom(resp)
    except ValueError or AttributeError:
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
    from src.TCPServer.tmp_test_impl import tcp_client, tcp_server
    # print("\n\n\n\n\nCECI EST LA REQUESTS GET ->", rq, tcp_server, tcp_client, "\n\n\n\n\n")
    try:
        print(rq.split('/', 3))
        path = "/" + rq.split('/', 3)[3]
        client_uuid = uuid.UUID(rq[7:43])
        if tcp_server is not None:
            client = tcp_server.clients_list.get_client_per_uuid(str(client_uuid))
            resp = client.get(route=path, json_obj=json_)
            print("ET LA REPONSE : ", resp, "\n\n\n\n\n")
            return ResponseCustom(resp)
        if tcp_client is not None:
            # client = tcp_client.client
            resp = tcp_client.get(route=path, json_obj=json_)
            print("ET LA REPONSE : ", resp, "\n\n\n\n\n")
            return ResponseCustom(resp)
    except ValueError or AttributeError:
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
