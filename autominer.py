import requests
from time import sleep
from src.blockchain.tools import get


class AutoMiner:
    def __init__(self, cooldown, node_address):
        """
        Requests nodes
        :param cooldown: time between each call to mine (in seconds)
        :param node_address: list nodes ip_addresses.
        """
        self.cooldown = cooldown
        self.node_address = node_address

    def run(self):
        while True:
            response = get(
                f"http://{self.node_address}/block/new", json_={"spread": False}
            )
            if response is not None:
                print(f"[{response.status_code}] {response.text}")
            sleep(self.cooldown)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Program that automatically ask nodes to mine"
    )
    parser.add_argument(
        "--cooldown",
        "-c",
        type=float,
        help="time between each call to mine (in seconds)",
        default=3,
    )
    parser.add_argument(
        "--node_address",
        "-na",
        help="address of the node to mine",
        default="127.0.0.1:5000",
    )

    args = parser.parse_args()
    miner = AutoMiner(cooldown=args.cooldown, node_address=args.node_address)
    miner.run()
