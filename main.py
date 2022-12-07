from src.TCPServer.tcp_server import TCPServer
from src.TCPServer.tcp_client import TCPClient
from src.TCPServer import tmp_test_impl
from src.blockchain.urls import routes
from src.blockchain.rq_tools import post
import threading
import sys
import json



class TCPThread(threading.Thread):
    def __init__(self, tcp):
        super().__init__()
        self.tcp = tcp

    def run(self):
        self.tcp.run()


def debug_main(http:bool = False, tcp_serv:bool = False, tcp_cli:bool = False, server_settings: dict = None):
    if not http and not tcp_serv and not tcp_cli:
        return False
    # bc: BlockchainManager = BlockchainManager()
    if tcp_serv:
        print("start tcp server")
        tmp_test_impl.tcp_server = TCPServer("0.0.0.0", server_settings["tcp_server"]["port"], routes)
        thread = TCPThread(tmp_test_impl.tcp_server)
        thread.start()
    if tcp_cli:
        print("start tcp client")
        tmp_test_impl.tcp_client = TCPClient(server_settings["tcp_client"]["ip"], server_settings["tcp_client"]["port"], routes)
        print(tmp_test_impl.tcp_client.client.get_socket().getsockname())
        # tmp_test_impl.tcp_client.post("/nodes/register", 
        thread = TCPThread(tmp_test_impl.tcp_client)
        thread.start()
        post(f"http://{tmp_test_impl.tcp_client.client.uid}/nodes/register", json_={
            "node": "<unknown>",
            "spread": True,
            "register_back": True,
            "type": "all"
        })
    if http:
        from src.blockchain.config import Host
        from src.blockchain.server import app
        print("start http")
        app.run(
            host="0.0.0.0", port=Host().port, debug=False
        )  # if debug is True server is started twice
    


if __name__ == "__main__":
    print("Bjr ceci devrait être le tout tout premier print et je ne veux rien entendre d'autre à ce sujet")
    if len(sys.argv) == 1:
        debug_main(http=True)
    elif len(sys.argv) == 2:
        with open(sys.argv[1], "r") as f:
            server_settings = json.load(f)
            print(server_settings)
            debug_main(
                http=server_settings["protocols"]["http"],
                tcp_serv=server_settings["protocols"]["tcp_server"],
                tcp_cli=server_settings["protocols"]["tcp_client"],
                server_settings=server_settings
            )
