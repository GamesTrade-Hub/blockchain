from argparse import ArgumentParser
from src.server import app, Blockchain
from src.config import NodeType

# FIXME regrouper ça et wsgi en mettant en place config

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-t', '--type', default='all', type=str, help='Type of node (all|miner|manager)', choices=['all', 'miner', 'manager'])
    args = parser.parse_args()

    port = args.port

    bc = Blockchain()
    bc.type = NodeType(args.type)
    app.run(host='0.0.0.0', port=port)

