import json
from sys import argv

# Open prod.config.json and change the following:
#   - "private_key": "{private_key}",
#   - "public_key": "{public_key}".

file = argv[1]
private_key = argv[2]
public_key = argv[3]

with open(file, "r") as f:
    config = json.load(f)
    config["private_key"] = private_key
    config["public_key"] = public_key
with open(file, "w") as f:
    json.dump(config, f, indent=4)
