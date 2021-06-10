FROM python:3.9.1 as base

MAINTAINER "Cyprien Ricque" "cyprien.ricque@epitech.eu"

COPY . /blockchain
WORKDIR /blockchain

RUN apt-get clean \
    && apt-get -y update

RUN pip3 install --upgrade pip \
    && apt-get -y install python3-dev \
    && apt-get -y install build-essential


FROM base as dev

RUN pip install -r requirements/dev.txt


FROM dev as test

RUN pip install unittest2


FROM base as prod

EXPOSE 5000

RUN apt-get -y install nginx \
    && pip install -r requirements/prod.txt

#COPY nginx.conf /etc/nginx

ENTRYPOINT ["gunicorn"]
CMD ["--bind", "0.0.0.0:5000", "wsgi:app"]
