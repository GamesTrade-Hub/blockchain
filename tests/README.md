Note that for these unit test you need these env variables
```
GTH_CONFIG=./configs/test.config.json;
PV_GTH={ask an admin};
PV_ADMIN={ask an admin};
```

How to launch all the tests

```
python -m unittest discover tests
```

How to launch one file

```
python -m unittest test.py
```

How to launch one test

```
python -m unittest testFile.testClass
```

How to get coverage

```
pip install coverage
coverage run -m unittest discover tests
coverage report (-m to get the missing line)
```

or
```
coverage html (to get a visual in a web page)
```


````bash
(blockchain_eip_dev) PS D:\Documents\Github\GTH\blockchain> coverage report
Name                                   Stmts   Miss  Cover
----------------------------------------------------------
src\__init__.py                            0      0   100%
src\blockchain\__init__.py                 0      0   100%
src\blockchain\block.py                  102     31    70%
src\blockchain\blockchain_manager.py     140     41    71%
src\blockchain\chain.py                   76     29    62%
src\blockchain\config.py                  70      4    94%
src\blockchain\keys.py                   139     25    82%
src\blockchain\network_interface.py      215     66    69%
src\blockchain\node.py                   178    121    32%
src\blockchain\rq_tools.py                35     28    20%
src\blockchain\server.py                 139     18    87%
src\blockchain\smart_contracts.py         99     14    86%
src\blockchain\tools.py                   26      3    88%
src\blockchain\transaction.py            214     50    77%
tests\__init__.py                          0      0   100%
tests\test_chain_creation.py              17      1    94%
tests\test_crypto.py                      31      1    97%
tests\test_mining.py                      30      1    97%
tests\test_nft_creation.py                25      1    96%
tests\test_smartscontracts.py             36      1    97%
tests\test_wallet.py                      24      5    79%
tests\testing_tools.py                    41      0   100%
----------------------------------------------------------
TOTAL                                   1637    440    73%
````