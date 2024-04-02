FROM ubuntu:22.04

WORKDIR /usr/src/

# Copy TF IaC  dir
COPY  ./iac/ .

# install python, pip and checkov
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.9 \
    python3-pip \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install checkov

# call checkov and pass args as you run
ENTRYPOINT ["checkov"]
