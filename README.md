# About

This project aims to create a tool to debug sparkplug communication with Edge Of Network Devices (EoN).

When launched, the `enki.py` script gives access to a shell with commands to manage topics subscriptions, list EoN and devices, craft metrics into payload. Type `help` to see the list of commands available.

Enki is the Sumerian god of water, knowledge, mischiefs, crafts and creations.

# Demo
[![asciicast](https://asciinema.org/a/lKGTwxDlLOYwGtsF1kecBLfa0.svg)](https://asciinema.org/a/lKGTwxDlLOYwGtsF1kecBLfa0)

# Docker image
## Build
```
docker build -t enki .
```
## Run
```
docker run -it --rm enki --server <mqtt broker hostname>
```
