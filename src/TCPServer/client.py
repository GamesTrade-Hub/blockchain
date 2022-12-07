import json
import logging
import queue
import socket
from uuid import uuid4


class BaseRoute:
    def __init__(self):
        pass

    def get(self, request_json: dict, client):
        return {"type": "response", "code": 404, "message": "Method not allowed"}

    def post(self, request_json, client):
        return {"type": "response", "code": 404, "message": "Method not allowed"}

    def parse_method(self, request_json, client):
        print(f"Receive request from {client.get_client_ip_address()}:{client.get_client_port()}")
        if request_json["method"] == "GET":
            return self.get(request_json, client)
        elif request_json["method"] == "POST":
            return self.post(request_json, client)
        return {"type": "response", "code": 400, "message": "Bad request"}


class HomeRoute(BaseRoute):
    def __init__(self):
        super().__init__()

    def get(self, request_json, client):
        return {"type": "response", "code": 200, "message": f"Success {request_json['payload']}"}

    def post(self, request_son, client):
        return {"type": "response", "code": 200, "message": "Finalement c'est bon"}


class Client:
    def __init__(self, sock: socket.socket, routes: dict, server: bool = False):
        logging.info("New client connected")
        self.uid = str(uuid4())
        self.routes = routes
        self.socket: socket.socket = sock
        self.server = server
        self.message_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.buffer = str()

    def get(self, route, json_obj):
        request = {
            "type": "request",
            "route": route,
            "method": "GET",
            "payload": json_obj
        }
        self.__add_to_send_list__(request)
        return self.get_resp()

    def post(self, route, json_obj):
        request = {
            "type": "request",
            "route": route,
            "method": "POST",
            "payload": json_obj
        }
        self.__add_to_send_list__(request)
        return self.get_resp()

    def __add_to_send_list__(self, json_dict: dict):
        json_bytes = str.encode(json.dumps(json_dict))
        # json_size = len(json_bytes).to_bytes(8, byteorder="big")
        self.message_queue.put(json_bytes)

    def get_socket(self) -> socket.socket:
        return self.socket

    def is_server(self) -> bool:
        return self.server
    
    def get_client_ip_address(self):
        return self.socket.getpeername()[0]
    
    def get_client_port(self):
        return self.socket.getpeername()[1]

    def read_socket(self):
        try:
            data = self.socket.recv(8)
            size = int.from_bytes(data, byteorder="big")
            # print(f"Size to read: {size}")
            data = self.socket.recv(size)
            # print(f"Data read : {data}")
        except BlockingIOError:
            logging.info("BlockingIOError catch")
            return False
        except MemoryError:
            logging.info("MemoryError catch")
            return False
        if data:
            # logging.debug(f"Data received : {data}")
            try:
                json_data = json.loads(data)
                if type(json_data) == str:
                    json_data = json.loads(json_data)
                try:
                    if json_data["type"] == "request" and json_data["route"] in self.routes:
                        response = self.routes[json_data["route"]]().parse_method(json_data, self)
                        self.__add_to_send_list__(response)
                    elif json_data["type"] == "response":
                        self.response_queue.put(json_data)
                    else:
                        self.__add_to_send_list__({"type": "response", "code": 404, "message": f"Route {json_data['route']} not found"})
                except KeyError:
                    self.__add_to_send_list__({"type": "response", "code": 400, "message": f"Bad request, key 'route', or 'type' missing in {json_data}"})
                # self.message_queue.put(data)
            except json.decoder.JSONDecodeError:
                logging.warning("wrong data")
            return True
        return False

    def send_data(self):
        try:
            json_obj = self.message_queue.get_nowait()
            if type(json_obj) is not bytes:
                json_bytes = str.encode(json.dumps(json_obj.decode()))
            else:
                json_bytes = json_obj
            json_size = len(json_bytes).to_bytes(8, byteorder="big")
            self.socket.send(json_size + json_bytes)
            return True
        except queue.Empty:
            return False

    def get_resp(self):
        try:
            resp = self.response_queue.get(timeout=10.0)
        except queue.Empty:
            return {"type": "response", "error": "timeout"}
        return resp


class ClientsList:
    def __init__(self, server_socket, routes: dict):
        server = Client(sock=server_socket, server=True, routes=routes)
        self.inputs = {server_socket: server}
        self.outputs = {}

    def add_client(self, client_socket: socket.socket, routes: dict):
        new_client = Client(sock=client_socket, routes=routes)
        self.inputs[client_socket] = new_client

    def remove_client(self, client: Client = None):
        logging.debug(f"Remove client : {client.socket.getsockname()}")
        if client is None:
            return
        try:
            client.socket.shutdown(socket.SHUT_RDWR)
            client.socket.close()
        except OSError:
            pass
        del self.inputs[client.socket]
        if client.socket in self.outputs.keys():
            del self.outputs[client.socket]

    def remove_client_outputs(self, client: Client = None):
        if client is None:
            return
        del self.outputs[client.socket]

    def add_client_output(self, client: Client):
        self.outputs[client.get_socket()] = client

    def get_inputs_socket_list(self) -> list:
        return [i for i in self.inputs]

    def get_outputs_socket_list(self) -> list:
        return [i for i in self.outputs]

    def get_client(self, sock: socket.socket) -> Client:
        return self.inputs[sock]
    
    def get_client_per_uuid(self, in_uuid: str) -> Client:
        for i in self.inputs.values():
            if i.uid == in_uuid:
                return i
        return None

    def get_all_clients(self, with_server=False):
        output = []
        try:
            for i in self.inputs:
                if with_server or not self.inputs[i].is_server():
                    output.append(self.inputs[i])
        except RuntimeError or KeyError:
            return []
        return output
