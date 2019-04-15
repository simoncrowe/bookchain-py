FROM python:3.7-alpine

RUN apk update && \
    apk -U upgrade && \
    apk add \
	postgresql-libs \
	gcc \
	musl-dev \
	postgresql-dev \
	jpeg-dev \
	zlib-dev \
        bash \
        supervisor && \
        mkdir /var/log/bookchain

COPY ./src /app
COPY ./requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt 

COPY ./docker/supervisord.conf /etc/supervisord/supervisord.conf

WORKDIR /app

ENV PYTHONPATH=/app


ENTRYPOINT ["supervisord", "-c", "/etc/supervisord/supervisord.conf"]
