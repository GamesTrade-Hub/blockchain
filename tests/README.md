Note that for these unit test you need these env variables
```
GTH_CONFIG=./configs/test.config.json;
PV_GTH={ask an admin};
PV_ADMIN={ask an admin};
```

How to launch all the tests

```
cd tests
python3 unittest discover .
```

How to launch one file

```
cd tests
python3 unittest test.py
```

How to launch one test

```
cd tests
python3 unittest testFile.testClass
```

How to get coverage

```
pip install coverage
cd tests
coverage run (--source=path ex: --source=../src) -m unittest discover
coverage report (-m to get the missing line)
```

or
```
coverage html (to get a visual in a web page)
```