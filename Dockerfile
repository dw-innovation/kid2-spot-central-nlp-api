ARG PYTHON=python3
ARG PYTHON_VERSION=3.8.13

FROM ubuntu:20.04

ENV http_proxy=ADD_PROXY
ENV https_proxy=ADD_PROXY

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get autoremove -y \
    && apt-get clean \
    && apt-get install -y python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

WORKDIR /app

COPY app /app

COPY requirements.txt /app

RUN pip install -r /app/requirements.txt

EXPOSE 8080

CMD exec uvicorn main:app --reload --port 8080 --host 0.0.0.0