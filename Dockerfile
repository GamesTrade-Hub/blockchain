FROM python:3.9.1 as base

COPY . /blockchain
WORKDIR /blockchain

RUN pip3 install --upgrade pip \
    pip install -r requirements.txt


FROM base as test

RUN pip install unittest2