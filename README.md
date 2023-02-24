# About

This project aims to create a tool to debug sparkplug communication with Edge Of Network Devices (EoN).

Enki is the Sumerian god of water, knowledge, mischiefs, crafts and creations.

## Running
```
export PYTHONPATH=${PYTHONPATH}:$(pwd)/tahu/python/core/
./enki.py
```
When launched, the `enki.py` script gives access to a shell with commands to manage topics subscriptions, list EoN and devices, craft metrics into payload. Type `help` to see the list of commands available.

# Demo
[![asciicast](https://asciinema.org/a/lKGTwxDlLOYwGtsF1kecBLfa0.svg)](https://asciinema.org/a/lKGTwxDlLOYwGtsF1kecBLfa0)

# Docker image
## Registry image
```
docker run -it --rm ghcr.io/siemaapplications/enki:v0.2.1 --server <mqtt broker hostname>
```

## Build image
```
docker build -t enki .
docker run -it --rm enki --server <mqtt broker hostname>
```

## mqtt broker
`enki` must connect to a broker which is specified on the command line with the `--server` argument (eg `test.mosquitto.org`).

If a broker is running on the host computer, the ip of the docker network interface can be supplied to `--server`:
```
docker run -it --rm ghcr.io/siemaapplications/enki:v0.2.1 --server $(ip -4 -br a s docker0 | awk '{print $3}' | cut -d/ -f1)
```

However, if the broker is hosted in a container, the enki instance must be connected to the network hosting the broker:
```
docker run -it --rm --network <docker network name> ghcr.io/siemaapplications/enki:v0.2.1 --server <container instance name>
```
Where `<docker network name>` can be seen in the output of `docker network ls` command and `<container instance name>` in the output of `docker ps`.
