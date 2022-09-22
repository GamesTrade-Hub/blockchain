from uuid import uuid4
import time
import requests
from flask import Flask, jsonify, request
import json
import sys
import signal
import logging

from src.interface.node_manager import NodesManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.setLevel(logging.DEBUG)


if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    gunicorn_logger.setLevel(logging.DEBUG)
    logger.handlers = gunicorn_logger.handlers
    logger.setLevel(gunicorn_logger.level)

logger.info("run blockchain/server.py")

nodes_manager = NodesManager()

# Instantiate the Node
it_app = Flask(__name__)


@it_app.route("/nodes/new", methods=["POST"])
def new_node():

    values = request.get_json()
    required = ["private_key"]

    if not all(k in values for k in required):
        return jsonify({"message": f'Missing value among {", ".join(required)}'}), 401

    response = {
        "message": "The new node is being created",
    }

    try:
        nodes_manager.create_node_instance(
            values["private_key"],
            values["region"] if "region" in values else "eu-west-3c"
        )
    except BaseException as e:
        return json.dumps(e), 201
    return json.dumps(response), 200


@it_app.route("/nodes/terminate", methods=["POST"])
def terminate():

    response = {
        "message": "node terminated",
    }
    values = request.get_json()

    required = ["id"]

    if not all(k in values for k in required):
        return jsonify({"message": f'Missing value among {", ".join(required)}'}), 400

    nodes_manager.terminate_instance(values["id"])

    return json.dumps(response), 200


@it_app.route("/nodes/terminate_all", methods=["POST"])
def terminate_all():

    response = {
        "message": "nodes terminated",
    }

    nodes_manager.terminate_all_instances()

    return json.dumps(response), 200


@it_app.route("/nodes/list", methods=["GET"])
def list_nodes():

    response = nodes_manager.get_running_instances()

    logger.debug(response)
    return json.dumps(response), 200


if __name__ == '__main__':
    it_app.run(
        host="0.0.0.0", port=5020, debug=False
    )  # if debug is True server is started twice
