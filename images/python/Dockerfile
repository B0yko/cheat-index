# Agent image for Python tasks: Python 3.12 with pytest, the Node 24 runtime and the pinned agent CLIs.
# Build from the images/ directory: docker build -f python/Dockerfile -t cheat-index/agent-python .
FROM node:24-bookworm-slim@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205 AS node

FROM node AS clis
COPY agent-clis.txt /tmp/agent-clis.txt
RUN npm install --global --no-audit --no-fund --prefix /opt/agents $(grep -v '^#' /tmp/agent-clis.txt) \
 && npm cache clean --force

FROM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
 && apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl git procps ripgrep \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir pytest==9.1.1
COPY --from=clis /opt/agents /opt/agents
COPY agent-clis.txt /opt/agents/agent-clis.txt
ENV PATH=/opt/agents/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1
RUN useradd --create-home --uid 1000 --shell /bin/bash agent \
 && mkdir /work && chown agent:agent /work
USER agent
WORKDIR /work
