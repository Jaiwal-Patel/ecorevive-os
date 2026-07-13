# ADR-001: Use a modular monolith

**Status:** Accepted

## Context

EcoRevive OS requires accounts, requests, assignments, handovers and impact data to remain transactionally consistent. The initial team is small and the platform must be understandable to future student or volunteer maintainers.

## Decision

Use one Django application divided into domain modules, with one PostgreSQL database and one React client.

## Consequences

Deployment and local development remain simple. Domain modules can later be extracted if real performance or organizational boundaries justify it.
