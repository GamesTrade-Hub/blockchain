import logging
import select
import socket
import time
import json
import threading

from src.TCPServer.client import Client


class RestartClient(Exception):
    pass


def send_data(sock, json_obj: dict):
    json_bytes = str.encode(json.dumps(json_obj))
    json_size = len(json_bytes).to_bytes(8, byteorder="big")
    sock.send(json_size)
    sock.send(json_bytes)


class TCPClient:
    def __init__(self, ip: str, port: int, routes: dict):
        self.ip = ip
        self.port = port
        self.routes = routes
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        sock.setblocking(False)
        self.running = True
        self.client = Client(sock=sock, routes=routes)
        print(f"Connection to {ip} {port} succeed")

    def get(self, route, json_obj):
        request = {
            "type": "request",
            "route": route,
            "method": "GET",
            "payload": json_obj
        }
        print(type(request), request)
        self.client.__add_to_send_list__(request)
        return self.client.get_resp()

    def post(self, route, json_obj):
        request = {
            "type": "request",
            "route": route,
            "method": "POST",
            "payload": json_obj
        }
        print(type(request), request)
        self.client.__add_to_send_list__(request)
        return self.client.get_resp()

    def run(self):
        while self.running:
            readable, writable, exceptionals = select.select([self.client.socket], [self.client.socket], [self.client.socket])
            if self.client.socket in readable:
                try:
                    self.client.read_socket()
                    # data = self.client.socket.recv(8)
                    # if len(data) == 0:
                    #     self.running = False
                    #     # self.client.socket.close()
                    #     # self.client.socket = None
                    #     # self.client.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    #     # self.client.socket.connect((self.ip, self.port))
                    #     # self.client.socket.setblocking(False)
                    # size = int.from_bytes(data, byteorder="big")
                    # data = self.client.socket.recv(size)
                    # json_data = json.loads(data)
                    # if type(json_data) is str:
                    #     json_data = json.loads(data)
                    # if json_data["type"] == "request":
                    #     print("Requête reçue")
                    # elif json_data["type"] == "response":
                    #     self.client.response_queue.put(json_data)
                except BlockingIOError:
                    logging.info("BlockingIOError catch")
                    return False
                except json.decoder.JSONDecodeError:
                    logging.info("JSONDecodeError")
                    return False
            if self.client.socket in writable:
                self.client.send_data()
            if self.client.socket in exceptionals:
                self.running = False


class RunTcpClient(threading.Thread):
    def __init__(self, tcp):
        super().__init__()
        self.tcp_class = tcp

    def run(self):
        self.tcp_class.run()


if __name__ == "__main__":
    tcp_class = TCPClient("127.0.0.1", 5000)
    thread = RunTcpClient(tcp_class)
    thread.start()
    for i in range(100):
        resp = tcp_class.client.get("/", {"test2": 1})
        print(f"aaaaa1 {resp}")
        resp = tcp_class.client.get("/", {"test2": 2})
        print(f"aaaaa2 {resp}")
        resp = tcp_class.client.get("/", {"test2": 3})
        print(f"aaaaa3 {resp}")
        # time.sleep(2)
        resp = tcp_class.client.get("/", {"test2": 4})
        print(f"aaaaa4 {resp}")
        resp = tcp_class.client.get("/", {"test2": 5})
        print(f"aaaaa5 {resp}")
        resp = tcp_class.client.post("/", {"test2": 6})
        print(f"aaaaa6 {resp}")
    tcp_class.running = False
    thread.join()
