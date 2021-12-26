docker run -it -v "/var/run/docker.sock:/var/run/docker.sock:rw" \
    -v "/home/yaniar/.docker/machine/certs:/home/yaniar/.docker/machine/certs" \
    multi-docker:latest /bin/sh