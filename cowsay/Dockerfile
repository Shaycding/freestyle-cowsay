FROM alpine:latest

RUN apk add --no-cache nodejs npm && adduser -D -u 10001 app

COPY . /home/app

WORKDIR /home/app/src

RUN npm install && chmod +x entry-point.sh && chown -R 10001:10001 /home/app

USER 10001

ENTRYPOINT  ["./entry-point.sh"]
