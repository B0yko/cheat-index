# Agent image for TypeScript tasks: Node 24 (native type stripping, node:test), python3 for helper scripts,
# and the pinned agent CLIs.
# Build from the images/ directory: docker build -f node/Dockerfile -t cheat-index/agent-node .
FROM node:24-bookworm-slim@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205 AS node

FROM node AS clis
COPY agent-clis.txt /tmp/agent-clis.txt
RUN npm install --global --no-audit --no-fund --prefix /opt/agents $(grep -v '^#' /tmp/agent-clis.txt) \
 && npm cache clean --force

FROM node
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl git procps python3 ripgrep \
 && rm -rf /var/lib/apt/lists/*
COPY --from=clis /opt/agents /opt/agents
COPY agent-clis.txt /opt/agents/agent-clis.txt
ENV PATH=/opt/agents/bin:$PATH
RUN usermod --login agent --move-home --home /home/agent node \
 && groupmod --new-name agent node \
 && mkdir /work && chown agent:agent /work
USER agent
WORKDIR /work
