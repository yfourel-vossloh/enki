FROM alpine:3.17.1
RUN apk update && apk upgrade && apk add git python3 py3-pip \
            && git clone --recurse-submodules https://github.com/SiemaApplications/enki \
            && pip install cmd2 paho-mqtt protobuf

RUN adduser --disabled-password enki
USER enki
ENV PYTHONPATH=/enki/tahu/client_libraries/python
WORKDIR /enki
ENTRYPOINT ["/enki/enki.py"]
