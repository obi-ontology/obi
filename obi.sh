#!/bin/sh

docker build --quiet --tag obi:latest .
#docker build --no-cache --tag obi:latest .
docker run --rm -it -p 5001:5000 -v $(pwd):/work -w /work obi:latest $@
