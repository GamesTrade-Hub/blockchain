FROM python:3.9.1 as base

MAINTAINER Cyprien Ricque "cyprien.ricque@epitech.eu"

RUN apt-get clean \
    && apt-get -y update

COPY requirements /tmp/requirements

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install python3-dev \
    && apt-get -y install build-essential

RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

ENV PATH="/home/appuser/.local/bin:${PATH}"

RUN /usr/local/bin/python -m pip install --upgrade pip \
    && /usr/local/bin/python -m pip install -r /tmp/requirements/common.txt --user

COPY . /home/appuser


FROM base as dev

RUN /usr/local/bin/python -m pip install -r /tmp/requirements/dev.txt --user


FROM dev as test

RUN /usr/local/bin/python -m pip install -r /tmp/requirements/test.txt --user


FROM base as prod

EXPOSE 5000

USER root
RUN apt-get -y install nginx
USER appuser

RUN /usr/local/bin/python -m pip install -r /tmp/requirements/prod.txt --user

#COPY nginx.conf /etc/nginx

RUN echo test

ENV PORT=$PORT
CMD gunicorn --bind 0.0.0.0:$PORT wsgi:app
