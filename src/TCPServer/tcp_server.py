import queue
import select
import socket
import logging

from src.TCPServer.client import Client, ClientsList


class TCPServer:
    def __init__(self, ip: str, port: int, routes: dict):
        self.routes = routes
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.setblocking(False)
        self.server.bind((ip, port))
        self.server.listen(5)
        logging.info(f"Server started on {ip}:{port}")
        self.clients_list = ClientsList(server_socket=self.server, routes=self.routes)
        self.inputs = [self.server]
        self.outputs = []
        self.message_queue = {}

    def _read_(self, readable):
        for i in readable:
            cli = self.clients_list.get_client(sock=i)
            if cli.is_server():
                new_socket, client_address = i.accept()
                new_socket.setblocking(False)
                self.clients_list.add_client(client_socket=new_socket, routes=self.routes)
                # self.inputs.append(new_socket)
                # self.message_queue[new_socket] = queue.Queue()
            else:
                try:
                    if cli.read_socket():
                        if cli.get_socket() not in self.clients_list.get_outputs_socket_list():
                            self.clients_list.add_client_output(cli)
                    else:
                        self.clients_list.remove_client(cli)
                except ConnectionResetError:
                    pass

    def _write_(self, writable):
        for i in writable:
            try:
                cli = self.clients_list.get_client(i)
                if not cli.send_data():
                    self.clients_list.remove_client_outputs(cli)
            except KeyError as e:
                logging.warning(f"KeyError {e.__cause__}")

    def _exceptionals_(self, exceptionals):
        for i in exceptionals:
            cli = self.clients_list.get_client(i)
            self.clients_list.remove_client(cli)

    def _run_(self):
        while self.clients_list.get_inputs_socket_list():
            readable, writable, exceptionals = select.select(self.clients_list.get_inputs_socket_list(), self.clients_list.get_outputs_socket_list(), self.clients_list.get_inputs_socket_list())
            self._read_(readable)
            self._write_(writable)
            self._exceptionals_(exceptionals)

    def _stop_server_(self):
        logging.info("Server Stopped.")
        for i in self.clients_list.get_inputs_socket_list():
            cli = self.clients_list.get_client(i)
            if not cli.is_server():
                self.clients_list.remove_client(cli)
        self.server.shutdown(socket.SHUT_RDWR)
        self.server.close()

    def run(self):
        try:
            self._run_()
        except KeyboardInterrupt or Exception as e:
            self._stop_server_()
