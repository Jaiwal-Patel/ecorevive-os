# API Guide

Interactive OpenAPI documentation is available at `/api/docs/` in a running environment.

## Public endpoints

- `GET /api/health/`
- `GET /api/public/config/`
- `GET /api/public/impact/`
- `GET /api/item-categories/`
- `POST /api/auth/register/`
- `POST /api/auth/token/`

## Authenticated resident endpoints

- `GET/PATCH /api/auth/me/`
- `POST /api/auth/change-password/`
- `GET/POST /api/collection-requests/`
- `GET/PATCH /api/collection-requests/{id}/`
- `POST /api/collection-requests/{id}/submit/`

## Administrator endpoints

- `POST /api/collection-requests/{id}/transition/`
- `/api/users/`
- `/api/organizations/`
- `/api/volunteer-profiles/`
- `/api/pickup-assignments/`
- `/api/handover-batches/`
- `/api/route-plans/optimize/`
- `/api/impact-metrics/`

## Governance endpoints

- `GET /api/governance/identities/`
- `GET /api/governance/audit-events/`
