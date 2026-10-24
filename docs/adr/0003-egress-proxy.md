# 3. One allow-listing egress proxy per run

Status: accepted

## Context
Agents must reach the model, and nothing else: package installs, web searches and real services would change what
is measured, and a blocked-environment task must stay blocked. We also want to see what agents try to reach.

## Decision
Each run gets its own Docker network created with `--internal` (no route out). On it sit the agent container, the
shared model gateway (attached under the alias `gateway`) and a per-run proxy container running
`runner/egress_proxy.py`: a small asyncio HTTP CONNECT and absolute-URI proxy that permits only the hosts the
adapter declares (normally none besides the gateway), answers everything else with 403, and logs every attempt as a
JSON line. Agents get `HTTP(S)_PROXY` pointing at it, `NO_PROXY=gateway,localhost,127.0.0.1` and `NODE_USE_ENV_PROXY=1`. A client that
ignores proxy settings still has no route out; such attempts fail without a log line.

## Consequences
- Attempted egress is recorded as a behaviour signal (`egress_attempt`), never as tampering.
- Hosts a harness contacts on its own (update checks, telemetry, catalogues) are measured on a no-op task, switched
  off through documented settings where possible, and excluded from the signal.
