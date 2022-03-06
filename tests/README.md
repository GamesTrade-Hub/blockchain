How to launch all the tests

* cd tests
* python3 inittest discover .

How to launch one file

* cd tests
* python3 inittest test.py

How to launch one test

* cd tests
* python3 inittest testFile.testClass

How to get coverage

* pip install coverage
* cd tests
* coverage run (--source=path ex: --source=../src) -m unittest discover
* coverage report (-m to get the missing line)

or
* coverage html (to get a visual in a web page)