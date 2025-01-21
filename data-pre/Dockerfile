# Use the specified Red Hat Universal Base Image 9 (UBI9)
FROM registry.access.redhat.com/ubi9/ubi as base

RUN dnf update -y && dnf install -y wget git
WORKDIR  /tmp
RUN wget https://github.com/tree-sitter/tree-sitter/releases/download/v0.24.3/tree-sitter-linux-x64.gz && gzip -d tree-sitter-linux-x64.gz && chmod +x tree-sitter-linux-x64 && mv tree-sitter-linux-x64 /usr/local/bin/tree-sitter
RUN git clone https://github.com/Hubro/tree-sitter-robot.git


FROM  registry.access.redhat.com/ubi9/nodejs-18-minimal
#install debugging tools 
USER root
RUN microdnf update -y && dnf install -y vim less iputils telnet && dnf clean all
USER 1001

COPY --from=base /usr/local/bin/tree-sitter /usr/local/bin/tree-sitter
COPY --from=base --chown=1001:1001 /tmp/tree-sitter-robot $HOME/tree-sitter-robot
WORKDIR $HOME

RUN mkdir -p $HOME/.config/tree-sitter/ /tmp/workbed
COPY grammar.js $HOME/tree-sitter-robot
COPY config.json $HOME/.config/tree-sitter/
COPY  --chown=1001:1001 scan.robot.sh $HOME/
RUN chmod +x  $HOME/scan.robot.sh
WORKDIR $HOME/tree-sitter-robot
RUN tree-sitter generate
CMD $HOME/scan.robot.sh /tmp/workbed/
