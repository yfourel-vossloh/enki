FROM alpine:3.17.1
COPY requirements.txt /tmp/
RUN apk update && apk upgrade && apk add python3 py3-pip \
            && pip install -r /tmp/requirements.txt && rm -f /tmp/requirements.txt

COPY tahu/ /enki/tahu/
COPY *.py /enki/
RUN adduser --disabled-password enki
USER enki
ENV PYTHONPATH=/enki/tahu/python/core
WORKDIR /enki
ENTRYPOINT ["/enki/enki.py"]
