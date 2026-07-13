# EcoRevive OS Architecture

## Architectural style

EcoRevive OS is a modular monolith. This is deliberate: the product has interconnected workflows, a small initial engineering team and a need for strong transactional consistency. Premature microservices would add deployment, security and observability complexity without improving the pilot.

## Runtime topology

```text
Browser
  └── React + TypeScript web application
        └── JSON/HTTPS
              └── Django REST API
                    ├── PostgreSQL
                    ├── Redis task queue
                    ├── Celery worker
                    ├── email provider
                    └── optional Meta WhatsApp Cloud API
```

## Backend modules

- `accounts`: identity, roles and protected governance principals
- `organizations`: corporate contributors and memberships
- `operations`: collection requests, items, volunteers, assignments and recycler handovers
- `logistics`: geospatial route plans and optimization baseline
- `impact`: editable, verifiable public metrics
- `notifications`: provider-neutral notification delivery
- `audit`: append-only application event trail
- `common`: shared models, permissions and public configuration

## Security boundaries

1. Authentication establishes identity.
2. backend permissions enforce authorization; hiding a frontend control is never considered authorization.
3. household addresses are returned only to request owners, assigned volunteers or authorized administrators.
4. protected governance principals cannot be deleted, deactivated or reassigned through ordinary application workflows.
5. public impact endpoints expose aggregate metrics only.

## Scaling path

The first scaling steps should be database indexing, background-task tuning, object storage and caching. Separate services should be considered only after measured bottlenecks justify them.
