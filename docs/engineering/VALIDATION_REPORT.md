# Validation Report — Version 0.1.0

Validation date: 2026-07-13

## Pass 1 — backend foundation

- generated and applied initial migrations;
- seeded categories and configurable impact metrics;
- ran Django system checks;
- ran Ruff linting;
- executed backend unit/API tests;
- confirmed route-baseline tests;
- confirmed ownership isolation and protected-account model rules.

## Pass 2 — integrated repository

- rebuilt a fresh SQLite database from migrations;
- bootstrapped `ujaiwal@outlook.com` as Founder Guardian;
- verified item-category and impact seed data;
- exercised public health, configuration and impact endpoints over HTTP;
- ran Django deployment checks with production security settings;
- validated development Compose, production Compose and GitHub Actions files as YAML;
- ran TypeScript checking, ESLint, Vitest and Vite production build;
- confirmed package-lock reproducibility;
- performed a basic repository secret-pattern review.

## Automated results at handoff

- Backend: 11 tests passing
- Backend measured coverage: approximately 75%
- Frontend: lint passing, tests passing, TypeScript build passing
- Django deployment check: no issues
- Migrations: no uncommitted model changes

## Environment limitation

The artifact environment used for assembly did not expose a Docker daemon, so the full Compose image build was not executed here. Dockerfiles and Compose YAML were reviewed and validated; GitHub Codespaces and GitHub Actions are the intended next execution environments.
