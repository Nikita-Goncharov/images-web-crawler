FROM python:3.11-slim

COPY . /app
# COPY ./requirements.txt /app/requirements.txt
WORKDIR /app

RUN apt update && apt install libcairo2 -y
RUN pip install -r ./requirements.txt
