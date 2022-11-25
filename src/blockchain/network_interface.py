from src.blockchain.blockchain_manager import BlockchainManager
from src.blockchain.blockchain_manager import Chain
from src.blockchain.tools import BcEncoder, hash__
from src.blockchain.keys import PublicKey, PrivateKey, PublicKeyContainer
from src.blockchain.config import Host, NodeType, conf, PUBLIC_KEY, config_file_path


import uuid
from urllib.parse import urlparse
from uuid import uuid4
from flask import jsonify, request
import time
import requests
import json
import sys
import signal
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.setLevel(logging.DEBUG)


if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    gunicorn_logger.setLevel(logging.DEBUG)
    logger.handlers = gunicorn_logger.handlers
    logger.setLevel(gunicorn_logger.level)

logger.info("run blockchain/network_interface.py")
logger.debug(f"Config file path: {config_file_path}")
logger.info(conf)


class NetworkInterface:
    def __init__(self):
        self.blockchain = BlockchainManager()
        self.blockchain.type = conf.type
        self.host = Host()
        Host().port = conf.port
        for n in conf.nodes:
            logger.debug(f"add node {n}")
            self.blockchain.add_node(n, register_back=True)
        self.replaced = self.blockchain.resolve_conflicts()

    @staticmethod
    def get_private_key():
        private_key = PrivateKey.generate().encode()
        response = {"key": f"{private_key}"}
        return response, 201

    @staticmethod
    def get_public_key_casual(request_json):
        values = request_json
        if values is None or "private_key" not in values:
            return "Error: Please supply a private key", 400
        private_key = PrivateKey(values.get("private_key"))
        public_key = PublicKeyContainer.casual_from_private_key(private_key).encode()
        response = {"key": f"{public_key}"}
        return response, 201

    @staticmethod
    def get_public_key_admin(request_json):
        values = request_json
        if values is None or "private_key" not in values:
            return "Error: Please supply a private key", 400

        required = ["private_key", "token", "gth_private_key"]
        if not all(k in values for k in required):
            print("return", f'Missing value among {", ".join(required)}', 400)
            return f'Missing value among {", ".join(required)}', 400

        private_key = PrivateKey(values.get("private_key"))
        token = values.get("token")
        gth_private_key = PrivateKey(values.get("gth_private_key"))

        public_key = PublicKeyContainer.token_admin_from_private_key(private_key, token, gth_private_key).encode()
        response = {"key": f"{public_key}"}
        return response, 201

    @staticmethod
    def get_public_key_miner(request_json):
        values = request_json
        if values is None or "private_key" not in values:
            return "Error: Please supply a private key", 400

        required = ["private_key", "gth_private_key"]
        if not all(k in values for k in required):
            print("return", f'Missing value among {", ".join(required)}', 400)
            return f'Missing value among {", ".join(required)}', 400

        private_key = PrivateKey(values.get("private_key"))
        gth_private_key = PrivateKey(values.get("gth_private_key"))

        public_key = PublicKeyContainer.miner_from_private_key(private_key, gth_private_key).encode()
        response = {"key": f"{public_key}"}
        return response, 201

    @staticmethod
    def get_node_public_key():
        public_key = PUBLIC_KEY
        response = {"key": f"{public_key}"}
        return response, 200

    @staticmethod
    def launch():
        response = {"message": f"node initialized"}
        return response, 200

    @staticmethod
    def status():
        response = {"message": "Node is OK"}
        return response, 200

    def new_transactions(self, request_json):
        values = request_json

        # Check that the required fields are in the POST'ed data
        required = ["sender", "recipient", "amount", "private_key", "token"]
        if not all(k in values for k in required):
            print("return", f'Missing value among {", ".join(required)}', 400)
            return f'Missing value among {", ".join(required)}', 400

        # print('new transaction sc', values['sc'] if 'sc' in values else "no sc")
        # Create a new transaction if the transaction is valid
        created, msg = self.blockchain.create_transaction(values, spread=True)
        if not created:
            return {"message": f"Transaction can't be created, Reason: {msg}"}, 401
        return {"message": f"ok"}, 201

    def create_nft(self, request_json):
        """
        :root_param token: the token that have to be used to buy the NFT
        :root_param nb: id of the nft to prevent nft having the same id
        :root_param private_key : private key of gth
        :return:
        """

        values = request_json
        required = ["token", "gth_private_key"]

        if not all(k in values for k in required):
            return {"message": f'Missing value among {", ".join(required)}'}, 401

        created, msg = self.blockchain.create_nft(
            token=values["token"],
            nb=str(values["nb"]) if "nb" in values else str(uuid4()),
            gth_private_key=values["gth_private_key"],
        )
        if not created:
            return f"Transaction can't be created, Reason: {msg}", 401
        return {"id": msg}, 201

    @staticmethod
    def create_item(request_json):
        """
        :root_param token: the token that have to be used to buy the item
        :root_param nb: id of the item to prevent items having the same id
        :return: token to use to identify the item in the blockchain
        """
        values = request_json
        required = ["token"]

        if not all(k in values for k in required):
            return {"message": f'Missing value among {", ".join(required)}'}, 400

        if '_' in values['token']:
            return {"message": f"token can't contain _"}, 400

        message = {
            "message": f"Item created, please use this token",
            "token": f'item_{hash__(str(values["nb"]) if "nb" in values else str(uuid4()))}_{values["token"]}',
        }
        return message, 201

    def add_transaction(self, request_json):
        values = request_json
        required = ["tx"]
        if not all(k in values for k in required):
            return f'Missing value among {", ".join(required)}', 400

        print("values", type(values), values)
        created, msg = self.blockchain.create_transaction(values["tx"], spread=False)
        if created:
            return "Transaction added", 201
        return msg, 401

    def chain(self):
        response = {
            "chain": self.blockchain.chain.__dict__(),
            "length": self.blockchain.chain_size,
        }
        return response, 200

    def ping(self):
        return {"pong": "oui", "waitingTxs": self.blockchain.txs.__dict__()}, 200

    def register_nodes(self, request_json, remote_addr):
        # TODO: C'est le bazar ici
        logging.debug("Register request received")

        message = "New node have been added"

        values = request_json
        required = ["node"]

        if not all(k in values for k in required):
            print("register request answered wrong")
            return {"message": f'Missing value among {", ".join(required)}'}, 400

        logger.info(f"Add node from {values}. Replace <unknown> with {remote_addr}")
        node = values.get("node").replace(
            "<unknown>", remote_addr
        )  # FIXME not really clean
        logger.info(f"New node value {node}. Add node blockchain.addNode")
        code = self.blockchain.add_node(
            node,
            type_=None if "type" not in values else values["type"],
            register_back=False
            if "register_back" not in values
            else values["register_back"],
            spread=False if "spread" not in values else values["spread"],
        )
        if code == 400:
            logger.warning(f"Node {node} not added")
            message = "ERROR: node not added"

        logger.info(f"All nodes {self.blockchain.nodes.__str__()}")

        return {"message": message, "total_nodes": self.blockchain.nodes.__str__()}, code

    def unregister(self, request_json, remote_addr):
        values = request_json
        required = ["port"]

        if not all(k in values for k in required):
            return {"message": f'Missing value among {", ".join(required)}'}, 400

        port = values["port"]

        rv = self.blockchain.nodes.unregister(f"{remote_addr}:{port}")

        return ("ok", 200) if rv else ("node not found", 400)

    def get_type(self):
        return {"type": self.host.type.value}

    def consensus(self):
        self.replaced = self.blockchain.resolve_conflicts()

        response = {
            "message": "Our chain is authoritative",
            "chain": self.blockchain.chain.__dict__(),
        }
        if self.replaced:
            response["message"] = ("Our chain was replaced",)

        return response, 200

    def get_nodes_list(self):
        nodes = self.blockchain.get_connected_nodes()
        return nodes.__dict__(), 200

    def new_block(self, request_json):
        """
        Creates a new block if there is enough transactions in the transaction pool.
        :root_param spread: if true and the current block does not have enough transactions in the transaction pool,
        the new block will be spread to the other nodes
        """

        logger.debug(f"Chain size: {self.blockchain.chain_size}")
        logger.debug("request.get_json()")
        values = request_json

        logger.debug(
            "blockchain.new_authority_block(spread=values and 'spread' in values and values['spread'])"
        )
        response, code = self.blockchain.new_authority_block(
            spread=values and "spread" in values and values["spread"]
        )

        logger.debug(f"response, code = {response, code}")
        return response, code

    def chain_found(self, request_json):
        values = request_json
        required = ["chain"]

        if not all(k in values for k in required):
            return {"message": f'Missing value among {", ".join(required)}'}, 400

        logging.info("Chain received", values["chain"])
        self.blockchain.replace_chain_if_better(Chain.from_dict(values["chain"]))
        return "ok", 200

    def get_balance(self, request_json):
        values = request_json

        if values is None or "user_id" not in values:
            return "Invalid request please specify user id", 400

        if "token" not in values:
            balance = self.blockchain.get_balance(values["user_id"])
        else:
            balance = self.blockchain.get_balance_by_token(values["user_id"], values["token"])
        return balance, 200

    # Decorator

    def high_level_handler(self, invalid: list = None, valid: list = None):
        if self.blockchain.type is None or self.blockchain.type == NodeType.UNKNOWN:
            self.blockchain.type = NodeType.ALL

        def decorator(fn):
            def inner__(*args, **kwargs):
                self.host.host = (
                    request.host
                    if "unknown" in self.host.host
                       or ("127.0.0.1" not in request.host and "0.0.0.0" not in request.host)
                    else self.host.host
                )

                if (valid is None or self.blockchain.type in valid) and (
                        invalid is None or self.blockchain.type not in invalid
                ):
                    return fn(*args, **kwargs)
                else:
                    msg = f'Invalid request for this node of type {self.blockchain.type.value}. Valid: {"empty" if valid is None else [i.value for i in valid]}. Invalid {"empty" if invalid is None else [i.value for i in invalid]}'
                    response = {"message": msg}
                    logger.info(msg)
                    return jsonify(response), 400

            # noinspection PyUnresolvedReferences
            namespace = sys._getframe(1).f_globals  # Emilien you did not see that
            name = f"{fn.__name__}_wrap"
            inner__.__name__ = name
            namespace[name] = inner__

            return inner__

        return decorator


