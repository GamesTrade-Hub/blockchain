import json
from sys import argv


def setup_argparse():
    """
    Set up the argparse module to parse the command line
    Arguments are :
    - config_file_path (cfg) string
    - private_key (pvk) Optional string
    - public_key (pbk) Optional string
    - nodes (nds) Optional list of string
    """
    import argparse
    parser = argparse.ArgumentParser(description="Update the miner keys")
    parser.add_argument("-cfg", "--config_file_path", type=str, help="Path to the config file", required=True)
    parser.add_argument("-pvk", "--private_key", type=str, help="Private key")
    parser.add_argument("-pbk", "--public_key", type=str, help="Public key")
    parser.add_argument("-nds", "--nodes", nargs="*", help="Nodes ips; ex: 20.188.57.81:5000")
    return parser


def update_values_in_config_file(private_key, public_key, nodes, config_file_path):
    with open(config_file_path, "r") as f:
        config = json.load(f)
        config["private_key"] = private_key or config["private_key"]
        config["public_key"] = public_key or config["public_key"]
        config["nodes"] = nodes or config["nodes"]
    with open(config_file_path, "w") as f:
        json.dump(config, f, indent=4)


parser = setup_argparse()
args = parser.parse_args(argv[1:])
update_values_in_config_file(args.private_key, args.public_key, args.nodes, args.config_file_path)

