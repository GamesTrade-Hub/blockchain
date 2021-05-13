FROM python:3.9.1

ADD . /blockchain
WORKDIR /blockchain

RUN pip3 install --upgrade pip \
    pip install -r requirements.txt


