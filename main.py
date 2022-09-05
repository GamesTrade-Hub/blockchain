from argparse import ArgumentParser
from src.blockchain.server import app, BlockchainManager
from src.blockchain.config import NodeType, Host


def debug_main():
    bc: BlockchainManager = BlockchainManager()
    app.run(
        host="0.0.0.0", port=Host().port, debug=False
    )  # if debug is True server is started twice


if __name__ == "__main__":
    debug_main()
