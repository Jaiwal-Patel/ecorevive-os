# ADR-002: Disclosed reserved governance identities

**Status:** Accepted

## Context

The founder plans to delegate daily operations while preserving continuity and emergency recovery. A covert privileged account would create an unacceptable security and governance risk.

## Decision

Implement a visible Founder Guardian and an optional disclosed Founder Recovery identity. Exclude the recovery identity from routine operational user lists, but show it to governance leaders in the executive security register. Protect both from ordinary deletion, deactivation and role reassignment.

## Consequences

Emergency authority is transparent and auditable. Infrastructure ownership and executive documentation remain necessary because no application rule can override a database or cloud root owner.
