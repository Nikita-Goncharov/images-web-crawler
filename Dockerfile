FROM python:3.11-slim

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN apt update && apt install libcairo2 -y
RUN pip install -r ./requirements.txt

COPY . /app
