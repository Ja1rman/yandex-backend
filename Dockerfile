FROM python:3.10-slim-bullseye

RUN apt update && apt install -y libpq-dev python3-dev && pip3 install sqlalchemy psycopg2-binary flask

COPY . .

