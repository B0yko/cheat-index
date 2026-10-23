# Verification image (also runs the egress proxy and the model gateway): Python 3.12 with pytest, PyYAML and
# httpx, the Node 24 runtime and the pinned TypeScript compiler used for test-file analysis. The cheat_index
# package is copied in at run time, so code changes never need an image rebuild.
# Build from the images/ directory: docker build -f verify/Dockerfile -t cheat-index/verify .
FROM node:24-bookworm-slim@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205 AS node

FROM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && npm install --global --no-audit --no-fund typescript@5.9.3 \
 && npm cache clean --force \
 && pip install --no-cache-dir pytest==9.1.1 pyyaml==6.0.3 httpx==0.28.1
ENV NODE_PATH=/usr/local/lib/node_modules \
    PYTHONPATH=/opt/ci \
    PYTHONDONTWRITEBYTECODE=1
RUN useradd --create-home --uid 1001 --shell /bin/bash verifier \
 && mkdir -p /opt/ci /v && chown verifier:verifier /opt/ci /v
USER verifier
WORKDIR /v
