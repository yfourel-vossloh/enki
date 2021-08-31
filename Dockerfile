FROM alpine:latest
RUN apk update && apk upgrade && apk add git python3 py3-pip \
            && ln -s /usr/bin/python3 /usr/bin/python \
            && git clone --recurse-submodules https://github.com/SiemaApplications/enki \
            && pip install cmd2 paho-mqtt protobuf

RUN adduser --disabled-password enki
USER enki
ENV PYTHONPATH=/enki/tahu/client_libraries/python
WORKDIR /enki
ENTRYPOINT ["/enki/enki.py"]
