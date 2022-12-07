from src.blockchain.network_interface import NetworkInterface
from src.blockchain.config import Host, NodeType, conf, PUBLIC_KEY, config_file_path

from src.TCPServer.client import BaseRoute

from uuid import uuid4

import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.setLevel(logging.DEBUG)

logger.info("run blockchain/tcp_protocol_routes.py")
logger.debug(f"Config file path: {config_file_path}")
logger.info(conf)

network_interface = NetworkInterface()

node_identifier = str(uuid4()).replace("-", "")
logger.info(f"Identifier: {node_identifier}")

class GetNewPrivateKey(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.get_private_key()
        return {"type": "response", "code": code, "message": response}


class GetNewPublicKeyCasual(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.get_public_key_casual(request_json=request_json["payload"])
        return {"type": "response", "code": code, "message": response}


class GetNewPublicKeyAdmin(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.get_public_key_admin(request_json=request_json["payload"])
        return {"type": "response", "code": code, "message": response}


class GetNewPublicKeyMiner(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.get_public_key_miner(request_json=request_json["payload"])
        return {"type": "response", "code": code, "message": response}


class GetNodePublicKey(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.get_node_public_key()
        return {"type": "response", "code": code, "message": response}


class Start(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.launch()
        return {"type": "response", "code": code, "message": response}


class Status(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.status()
        return {"type": "response", "code": code, "message": response}


class TransactionNew(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.new_transactions(request_json=request_json["payload"])
        if code == 201:
            network_interface.new_block({'spread': True})
        return {"type": "response", "code": code, "message": response}


class CreateNFT(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.create_nft(request_json=request_json["payload"])
        if code == 201:
            network_interface.new_block({'spread': True})
        return {"type": "response", "code": code, "message": response}


class CreateItem(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.create_item(request_json=request_json["payload"])
        return {"type": "response", "code": code, "message": response}


class TransactionAdd(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.add_transaction(request_json=request_json["payload"])
        return {"type": "response", "code": code, "message": response}


class Chain(BaseRoute):
    def get(self, request_json, client):
        response, code = network_interface.chain()
        return {"type": "response", "code": code, "message": response}


class Ping(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.ping()
        return {"type": "response", "code": code, "message": response}


class NodesRegister(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.register_nodes(request_json=request_json["payload"], remote_addr=client.uid)  # ATTENTION C'EST A IMPLEMENTER ET TRES RAPIDEMENT
        return {"type": "response", "code": code, "message": response}


class NodesUnregister(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.unregister(request_json=request_json["payload"], remote_addr=request_json["payload"]["node"])  # ATTENTION C'EST A IMPLEMENTER ET TRES RAPIDEMENT
        return {"type": "response", "code": code, "message": response}


class GetType(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.get_type()
        return {"type": "response", "code": code, "message": response}


class NodesResolve(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.consensus()
        return {"type": "response", "code": code, "message": response}


class NodesList(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.get_nodes_list()
        return {"type": "response", "code": code, "message": response}


class BlockNew(BaseRoute):
    def get(self, request_json, client):
        response, code = network_interface.new_block(request_json=request_json["payload"])
        return {"type": "response", "code": code, "message": response}
    
    def post(self, request_json, client):
        response, code = network_interface.new_block(request_json=request_json["payload"])
        return {"type": "response", "code": code, "message": response}


class ChainFound(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.chain_found(request_json=request_json["payload"])
        return {"type": "response", "code": code, "message": response}


class GetBalance(BaseRoute):
    def post(self, request_json, client):
        response, code = network_interface.get_balance(request_json=request_json["payload"])
        return {"type": "response", "code": code, "message": response}


{
    "nodes": [
        "http://e50d20e0-ec74-4b9d-9215-70baf28d81b4:5001"
    ]
}

{
    "nodes": [
        "http://5693e8da-c23e-4607-87fe-e5b57aad976a"
    ]
}