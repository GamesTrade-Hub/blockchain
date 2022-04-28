from src.blockchain import Blockchain
from src.blockchain import Chain
from src.tools import BcEncoder, hash__
from src.keys import PublicKey, PrivateKey
from src.config import Host, NodeType, Config

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

logger.info("RUN SERVER.PY")

conf: Config = Config.from_file('config.json')
logger.info(conf)

# Instantiate the Blockchain
host = Host()
blockchain = Blockchain()
blockchain.type = conf.type

Host().port = conf.port

for n in conf.nodes:
    logging.debug(f'add node {n}')
    blockchain.addNode(n, register_back=True)

replaced = blockchain.resolveConflicts()

# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')
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
#
# signal.signal(signal.SIGINT, handler)
# signal.signal(signal.SIGTERM, handler)


def high_level_handler(invalid: list = None, valid: list = None):
    if blockchain.type is None or blockchain.type == NodeType.UNKNOWN:
        blockchain.type = NodeType.ALL

    def decorator(fn):
        def inner__(*args, **kwargs):
            host.host = request.host

            if (valid is None or blockchain.type in valid) and (invalid is None or blockchain.type not in invalid):
                return fn(*args, **kwargs)
            else:
                msg = f'Invalid request for this node of type {blockchain.type.value}. Valid: {"empty" if valid is None else [i.value for i in valid]}. Invalid {"empty" if invalid is None else [i.value for i in invalid]}'
                response = {'message': msg}
                logger.info(msg)
                return jsonify(response), 400

        # noinspection PyUnresolvedReferences
        namespace = sys._getframe(1).f_globals  # Emilien you did not see that
        name = f'{fn.__name__} + _wrap'
        inner__.__name__ = name
        namespace[name] = inner__

        return inner__

    return decorator


@app.route('/get_new_private_key', methods=['GET'])
@high_level_handler(invalid=[NodeType.MINER])
def get_private_key():
    private_key = PrivateKey.generate(encoded=True)
    response = {'key': f'{private_key}'}
    return jsonify(response), 201


@app.route('/get_new_public_key', methods=['GET'])
@high_level_handler(invalid=[NodeType.MINER])
def get_public_key():
    values = request.get_json()
    if values is None or 'private_key' not in values:
        return "Error: Please supply a private key", 400
    private_key = values.get('private_key')
    public_key = PublicKey.generate_from_private_key(private_key, encoded=True)
    response = {'key': f'{public_key}'}
    return jsonify(response), 201


@app.route('/start', methods=['GET'])
@high_level_handler()
def launch():
    response = {'message': f'node initialized'}
    return jsonify(response), 200


@app.route('/status', methods=['GET'])
@high_level_handler()
def status():

    response = {'message': f'Node is OK'}
    return jsonify(response), 200


@app.route('/transaction/new', methods=['POST'])
@high_level_handler(invalid=[NodeType.MINER])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount', 'private_key', 'token']
    if not all(k in values for k in required):
        print('return', f'Missing value among {", ".join(required)}', 400)
        return f'Missing value among {", ".join(required)}', 400

    # print('new transaction sc', values['sc'] if 'sc' in values else "no sc")
    # Create a new transaction if the transaction is valid
    created, msg = blockchain.createTransaction(values, spread=True)
    if not created:
        return jsonify({'message': f"Transaction can't be created, Reason: {msg}"}), 401
    return jsonify({'message': f'ok'}), 201


@app.route('/create_nft', methods=['POST'])
@high_level_handler(invalid=[NodeType.MINER])
def create_nft():
    """
    :root_param token: the token that have to be used to buy the NFT
    :root_param nb: id of the nft to prevent nft having the same id
    :root_param private_key : private key of gth
    :return:
    """


    values = request.get_json()
    required = ['token', 'nb', 'gth_private_key']

    if not all(k in values for k in required):
        return jsonify({'message': f'Missing value among {", ".join(required)}'}), 400

    created, msg = blockchain.createNFT(token=values['token'],
                                        nb=values['nb'],
                                        gth_private_key=values['gth_private_key'])
    if not created:
        return f'Transaction can\'t be created, Reason: {msg}', 401
    return jsonify({'id': msg}), 201


@app.route('/transaction/add', methods=['POST'])
@high_level_handler()
def add_transaction():

    values = request.get_json()

    required = ['tx']
    if not all(k in values for k in required):
        return f'Missing value among {", ".join(required)}', 400

    print("values", type(values), values)
    created, msg = blockchain.createTransaction(values['tx'], spread=False)
    if created:
        return 'Transaction added', 201
    return msg, 401


@app.route('/create_item', methods=['POST'])
@high_level_handler(invalid=[NodeType.MINER])
def create_item():
    """
    :root_param token: the token that have to be used to buy the item
    :root_param nb: id of the item to prevent items having the same id
    :return: token to use to identify the item in the blockchain
    """
    values = request.get_json()
    required = ['token', 'nb']

    if not all(k in values for k in required):
        return jsonify({'message': f'Missing value among {", ".join(required)}'}), 400

    return json.dumps({
        'message': f'Item created, please use this token',
        'token': f'item_{hash__(str(values["nb"]))}_{values["token"]}'
    }), 201


@app.route('/chain', methods=['GET'])
@high_level_handler()
def chain():

    response = {
        'chain': blockchain.chain.__dict__(),
        'length': blockchain.chain_size,
    }
    return json.dumps(response), 200


@app.route('/ping', methods=['GET'])
@high_level_handler()
def ping():

    return json.dumps({'pong': 'oui',
                       'waitingTxs': blockchain.txs.__dict__()}), 200


@app.route('/nodes/register', methods=['POST'])
@high_level_handler()
def register_nodes():
    logging.debug("Register request received")

    message = 'New node have been added'

    values = request.get_json()
    required = ['node']

    if not all(k in values for k in required):
        print("register request answered wrong")
        return jsonify({'message': f'Missing value among {", ".join(required)}'}), 400

    logger.info(f'Add node from {values}. Replace <unknown> with {request.remote_addr}')
    node = values.get('node').replace('<unknown>', request.remote_addr)  # FIXME not really clean
    logger.info(f"New node value {node}. Add node blockchain.addNode")
    code = blockchain.addNode(node,
                              type_=None if 'type' not in values else values['type'],
                              register_back=False if 'register_back' not in values else values['register_back'],
                              spread=False if 'spread' not in values else values['spread']
                              )
    if code == 400:
        logger.warning(f"Node {node} not added")
        message = "ERROR: node not added"

    logger.info(f"All nodes {blockchain.nodes.__str__()}")

    return jsonify({
        'message': message,
        'total_nodes': blockchain.nodes.__str__()}), code


@app.route('/nodes/unregister', methods=['POST'])
@high_level_handler()
def unregister():

    values = request.get_json()
    required = ['port']

    if not all(k in values for k in required):
        return jsonify({'message': f'Missing value among {", ".join(required)}'}), 400

    port = values['port']

    rv = blockchain.nodes.unregister(f'{request.remote_addr}:{port}')

    return ('ok', 200) if rv else ('node not found', 400)


@app.route('/get_type', methods=['GET'])
@high_level_handler()
def get_type():

    return jsonify({'type': host.type.value}), 200


@app.route('/nodes/resolve', methods=['GET'])
@high_level_handler()
def consensus():

    replaced = blockchain.resolveConflicts()

    response = {
        'message': 'Our chain is authoritative',
        'chain': blockchain.chain.__dict__()
    }
    if replaced:
        response['message'] = 'Our chain was replaced',

    return json.dumps(response), 200


@app.route("/nodes/list", methods=['GET'])
@high_level_handler()
def get_nodes_list():
    nodes = blockchain.getConnectedNodes()
    return jsonify(nodes.__dict__()), 200


@app.route('/mine', methods=['GET'])
@high_level_handler(invalid=[NodeType.MANAGER])
def mine():

    values = request.get_json()

    if values and 'spread' in values and values['spread'] is True:
        response, code = blockchain.mine(spread=True)
    else:
        response, code = blockchain.mine(spread=False)

    return json.dumps(response), code


@app.route('/do_not_use/end_mining_process', methods=['GET'])
@high_level_handler(invalid=[NodeType.MANAGER])
def end_mining_process():

    response, code = blockchain.updateMiningState()

    return json.dumps(response), code


@app.route('/chain_found', methods=['POST'])
@high_level_handler()
def chain_found():

    values = request.get_json()
    required = ['chain']

    if not all(k in values for k in required):
        return jsonify({'message': f'Missing value among {", ".join(required)}'}), 400

    logging.info('Chain received', values['chain'])
    blockchain.replaceChainIfBetter(Chain.from_dict(values['chain']))
    return 'ok', 200


@app.route("/get_balance", methods=['GET'])
@high_level_handler()
def get_balance():

    values = request.get_json()

    if values is None or 'user_id' not in values:
        return 'Invalid request please specify user id', 400

    balance = blockchain.getBalance(values['user_id'])
    return jsonify(balance), 200


@app.route("/get_balance_by_token", methods=['POST'])
@high_level_handler()
def get_balance_by_token():

    values = request.get_json()

    if values is None or 'user_id' not in values or 'token' not in values:
        return 'Invalid request please specify user id', 400

    balance = blockchain.getBalanceByToken(values['user_id'], values['token'])
    return jsonify({'balance': balance}), 200

