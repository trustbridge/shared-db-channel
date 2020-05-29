FROM python:3.8

WORKDIR /app

RUN apt-get update && \
    apt-get -y install graphviz && \
    apt-get -y install enchant && \
    apt-get -y install plantuml

RUN mkdir -p docs
COPY ./docs/requirements.txt docs/
RUN pip install --no-cache-dir -r docs/requirements.txt
