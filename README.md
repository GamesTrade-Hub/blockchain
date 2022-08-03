# Blockchain

This blockchain is used to manage items, nft and tokens of a game.
Since the needed package fastecdsa is not available on Windows, the nodes cannot be run in 

### Starting

````bash
python3 main.py -p [port number (default 5000)] -t [node type (default: all)]
````

for further information see
````bash
python3 main.py -h
````

### Convert python file to .exe script

First install the required lib using pip
````bash
pip install auto-py-to-exe
````

Then run
````bash
rm -rf ./bin/* && cd bin ; pyinstaller --noconfirm --onefile --console  "../main.py" -n node
````
and follow the instructions
