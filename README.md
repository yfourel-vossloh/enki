# About

This project aims to create a tool to debug sparkplug communication with Edge Of Network Devices (EoN).

Enki is the Sumerian god of water, knowledge, mischiefs, crafts and creations.

## Running
```
export PYTHONPATH=${PYTHONPATH}:$(pwd)/tahu/client_libraries/python
./enki.py
```
When launched, the `enki.py` script gives access to a shell with commands to manage topics subscriptions, list EoN and devices, craft metrics into payload. Type `help` to see the list of commands available.

# Demo
[![asciicast](https://asciinema.org/a/lKGTwxDlLOYwGtsF1kecBLfa0.svg)](https://asciinema.org/a/lKGTwxDlLOYwGtsF1kecBLfa0)

# Docker image
##
## Build
```
docker build -t enki .
```
If you do not want t build the docker image, you can pull it from container registry.
## Run
If you have built the image:
```
docker run -it --rm enki --server <mqtt broker hostname>
```

Pull the image from registry:
```
docker run -it --rm ghcr.io/siemaapplications/enki:<tag> --server <mqtt broker hostname>
```
> :bulb: in the above commands, replace `<tag>` and `<mqtt broker hostname>` with the appropriate values.  
> `mqtt broker hostname` should be the ip of the docker network interface if a broker is running on the host:  
> `ip -4 -br a s docker0 | awk '{print $3}' | cut -d/ -f1`  
