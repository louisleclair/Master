FROM nginx:1.15-alpine

RUN apk update
RUN apk add openssl

RUN rm -f /etc/nginx/conf.d/*
RUN mkdir /certs/
RUN mkdir /www
#RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /certs/nginx-selfsigned.key -out /certs/nginx-selfsigned.crt

COPY index.html /www
COPY default.conf /etc/nginx/conf.d/default.conf
COPY request.key /certs
COPY request.crt /certs