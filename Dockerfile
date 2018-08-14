FROM python:2.7

MAINTAINER Mikhail Borisov <baobab-borisov@mail.ru>

ENV PYTHONUNBUFFERED 1

RUN apt-get update

RUN mkdir -p /code
WORKDIR /code
COPY . /code/
RUN pip install -r requirements.txt
RUN source eComEnv/bin/activate



