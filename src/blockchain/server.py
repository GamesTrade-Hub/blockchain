from src.blockchain.rq_tools import get
from src.blockchain.blockchain_manager import BlockchainManager
from src.blockchain.blockchain_manager import Chain
from src.blockchain.network_interface import NetworkInterface
from src.blockchain.keys import PublicKey, PrivateKey
from src.blockchain.config import Host, NodeType, conf, PUBLIC_KEY, config_file_path

import uuid
from urllib.parse import urlparse
from uuid import uuid4
import time
import requests
from flask import Flask, jsonify, request
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


logger.info("run blockchain/server.py")
logger.debug(f"Config file path: {config_file_path}")

logger.info(conf)

# Instantiate the Blockchain
# # host = Host()
# # blockchain = BlockchainManager()
# # blockchain.type = conf.type
# #
# # Host().port = conf.port
# #
# # for n in conf.nodes:
# #     logger.debug(f"add node {n}")
# #     blockchain.add_node(n, register_back=True)
# #
# # replaced = blockchain.resolve_conflicts()

# Instantiate the Node
app = Flask(__name__)

network_interface = NetworkInterface()

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace("-", "")
logger.info(f"Identifier: {node_identifier}")
# client = docker.DockerClient()
# container = client.containers.get("magical_meitner")
# ip_add = container.attrs['NetworkSettings']['IPAddress']
# print("ip_add", ip_add)


# def handler(signalNumber, frame):
#     global blockchain
#     print(f'EXIT REQUIRED signal number {signalNumber} fame {frame}', flush=True, file=sys.stderr)
#     blockchain.__del__()
#     sys.exit(1)
#
# signal.signal(signal.SIGINT, handler)
# signal.signal(signal.SIGTERM, handler)


# def high_level_handler(invalid: list = None, valid: list = None):
#     if blockchain.type is None or blockchain.type == NodeType.UNKNOWN:
#         blockchain.type = NodeType.ALL
#
#     def decorator(fn):
#         def inner__(*args, **kwargs):
#             host.host = (
#                 request.host
#                 if "unknown" in host.host
#                 or ("127.0.0.1" not in request.host and "0.0.0.0" not in request.host)
#                 else host.host
#             )
#
#             if (valid is None or blockchain.type in valid) and (
#                 invalid is None or blockchain.type not in invalid
#             ):
#                 return fn(*args, **kwargs)
#             else:
#                 msg = f'Invalid request for this node of type {blockchain.type.value}. Valid: {"empty" if valid is None else [i.value for i in valid]}. Invalid {"empty" if invalid is None else [i.value for i in invalid]}'
#                 response = {"message": msg}
#                 logger.info(msg)
#                 return jsonify(response), 400
#
#         # noinspection PyUnresolvedReferences
#         namespace = sys._getframe(1).f_globals  # Emilien you did not see that
#         name = f"{fn.__name__}_wrap"
#         inner__.__name__ = name
#         namespace[name] = inner__
#
#         return inner__
#
#     return decorator


@app.route("/get_new_private_key", methods=["GET"])
@network_interface.high_level_handler(invalid=[NodeType.MINER])
def get_private_key():
    response, code = network_interface.get_private_key()
    return jsonify(response), code


@app.route("/get_new_public_key_casual", methods=["GET"])
@network_interface.high_level_handler(invalid=[NodeType.MINER])
def get_public_key_casual():
    response, code = network_interface.get_public_key_casual(request_json=request.get_json())
    return jsonify(response), code


@app.route("/get_new_public_key_admin", methods=["GET"])
@network_interface.high_level_handler(invalid=[NodeType.MINER])
def get_public_key_admin():
    response, code = network_interface.get_public_key_admin(request_json=request.get_json())
    return jsonify(response), code


@app.route("/get_new_public_key_miner", methods=["GET"])
@network_interface.high_level_handler(invalid=[NodeType.MINER])
def get_public_key_miner():
    response, code = network_interface.get_public_key_miner(request_json=request.get_json())
    return jsonify(response), code


@app.route("/get_node_public_key", methods=["GET"])
@network_interface.high_level_handler()
def get_node_public_key():
    response, code = network_interface.get_node_public_key()
    return jsonify(response), code


@app.route("/start", methods=["GET"])
@network_interface.high_level_handler()
def launch():
    response, code = network_interface.launch()
    return jsonify(response), code


@app.route("/status", methods=["GET"])
@network_interface.high_level_handler()
def status():
    response, code = network_interface.status()
    return jsonify(response), code


@app.route("/transaction/new", methods=["POST"])
@network_interface.high_level_handler(invalid=[NodeType.MINER])
def new_transaction():
    response, code = network_interface.new_transactions(request_json=request.get_json())
    if code == 201:
        get(f"http://127.0.0.1:{Host().port}/block/new", data={'spread': True}, timeout=0.0001)
        # network_interface.new_block({'spread': True})
    return jsonify(response), code


@app.route("/create_nft", methods=["POST"])
@network_interface.high_level_handler(invalid=[NodeType.MINER])
def create_nft():
    response, code = network_interface.create_nft(request_json=request.get_json())
    if code == 201:
        get(f"http://127.0.0.1:{Host().port}/block/new", data={'spread': True}, timeout=0.0001)
    return jsonify(response), code


@app.route("/create_item", methods=["POST"])
@network_interface.high_level_handler(invalid=[NodeType.MINER])
def create_item():
    response, code = network_interface.create_item(request_json=request.get_json())
    return json.dumps(response), code


@app.route("/transaction/add", methods=["POST"])
@network_interface.high_level_handler()
def add_transaction():
    response, code = network_interface.add_transaction(request_json=request.get_json())
    return response, code


@app.route("/chain", methods=["GET"])
@network_interface.high_level_handler()
def chain():
    response, code = network_interface.chain()
    return json.dumps(response), code


@app.route("/ping", methods=["GET"])
@network_interface.high_level_handler()
def ping():
    response, code = network_interface.ping()
    return json.dumps(response), code


@app.route("/nodes/register", methods=["POST"])
@network_interface.high_level_handler()
def register_nodes():
    response, code = network_interface.register_nodes(request_json=request.get_json(), remote_addr=request.remote_addr)
    return json.dumps(response), code


@app.route("/nodes/unregister", methods=["POST"])
@network_interface.high_level_handler()
def unregister():
    response, code = network_interface.unregister(request_json=request.get_json(), remote_addr=request.remote_addr)
    return response, code


@app.route("/get_type", methods=["GET"])
@network_interface.high_level_handler()
def get_type():
    response = network_interface.get_type()
    return response, 200


@app.route("/nodes/resolve", methods=["GET"])
@network_interface.high_level_handler()
def consensus():
    response, code = network_interface.consensus()
    return json.dumps(response), code


@app.route("/nodes/list", methods=["GET"])
@network_interface.high_level_handler()
def get_nodes_list():
    response, code = network_interface.get_nodes_list()
    return jsonify(response), code


@app.route("/block/new", methods=["GET", "POST"])
@network_interface.high_level_handler(invalid=[NodeType.MANAGER])
def new_block():
    response, code = network_interface.new_block(request_json=request.json)
    return json.dumps(response), code


@app.route("/chain_found", methods=["POST"])
@network_interface.high_level_handler()
def chain_found():
    response, code = network_interface.chain_found(request_json=request.get_json())
    return response, code


@app.route("/get_balance", methods=["GET"])
@network_interface.high_level_handler()
def get_balance():
    response, code = network_interface.get_balance(request_json=request.get_json())
    return jsonify(response), code
