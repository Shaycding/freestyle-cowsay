FROM alpine:latest

COPY . ./home/app

WORKDIR ./home/app/src

RUN chmod +x entry-point.sh

ENTRYPOINT  ["./entry-point.sh"]
