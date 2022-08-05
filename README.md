# Blockchain

This blockchain is used to manage items, nft and tokens of a game.
Since the needed package fastecdsa is not available on Windows, the nodes cannot be run on windows.

### Start

Install dependencies
```bash
pip3 install -r requirements/dev.txt
```

Run a node in debug mode using configuration configs/dev.config.json (default config file)
To change the config file, set GTH_CONFIG environment variable to the path of the config file.
```bash
````bash
python3 main.py
````

### Deploy

The deployment is done with github actions when a merge to main is done.
To see how it works, check the script deploy.sh.


### Test

You can test your environment by running the tests
```bash
GTH_CONFIG=configs/test.config.json python3 -m unittest discover -s tests -p 'test_*.py'
```

### Documentation

Documentation is generated using Spinx.
To install it, run the following command:
```bash
sudo apt-get install python3-sphinx
```