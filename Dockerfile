FROM alpine:3.17.1
RUN apk update && apk upgrade && apk add python3 py3-pip \
            && pip install cmd2 paho-mqtt protobuf

COPY tahu/ /enki/tahu/
COPY *.py /enki/
RUN adduser --disabled-password enki
USER enki
ENV PYTHONPATH=/enki/tahu/python/core
WORKDIR /enki
ENTRYPOINT ["/enki/enki.py"]
