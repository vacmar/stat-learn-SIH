# ADR 0001: Exasol Personal on macOS (not docker-db)

## Status

Accepted

## Context

Apple Silicon Macs struggle with `exasol/docker-db` (amd64): port 8563 often never becomes healthy, blocking local development.

## Decision

Use **Exasol Personal** via `exakit start` on the host for macOS development. Docker Compose runs app services only; backend connects to `host.docker.internal:8563`.

The `docker-exasol` compose profile remains for Linux/CI experiments but is not the default Mac path.

## Consequences

- Developers install Exasol Personal locally and manage password via `EXASOL_PASSWORD_FILE`.
- Documentation and root README must describe this flow explicitly.
- CI unit tests should set `EXASOL_ENABLED=false` when no Exasol instance is provisioned.
