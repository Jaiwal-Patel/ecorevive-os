# EcoRevive OS

**Today's Actions. Tomorrow's Impact.**

EcoRevive OS is an open-source operating platform for community-led e-waste collection in Dubai. It replaces fragmented forms, calls, spreadsheets, and chat messages with a traceable workflow for residents, organizations, volunteers, administrators, and certified recycling partners.

## Included in this repository

- React + TypeScript responsive web application
- Django REST API with PostgreSQL support
- JWT authentication and role-based authorization
- Household and corporate collection requests
- Multi-item e-waste inventory
- Volunteer profiles and pickup assignments
- Recycler handover records and traceability
- Public impact metrics that administrators can update over time
- Transparent route-order optimization baseline
- Email notifications and optional Meta WhatsApp Cloud API integration
- Founder Guardian and disclosed Founder Recovery governance identities
- Append-only application audit events
- Docker Compose, GitHub Codespaces, GitHub Actions, tests, and deployment guides

## Governance model

EcoRevive OS has two reserved governance roles:

- **Founder Guardian** — long-term constitutional platform authority.
- **Founder Recovery** — a dormant, disclosed emergency identity, excluded from routine operational screens but visible in the dedicated governance interface.

The recovery role is not a covert backdoor. Its existence and scope are documented in [`docs/governance/EXECUTIVE_GOVERNANCE.md`](docs/governance/EXECUTIVE_GOVERNANCE.md). Both identities are protected from deletion, deactivation, or role changes through ordinary application workflows.

## Technology

| Layer | Choice |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, Django, Django REST Framework |
| Database | PostgreSQL |
| Background jobs | Celery + Redis |
| Authentication | JWT |
| Development | Docker + GitHub Codespaces |
| CI | GitHub Actions |
| Initial deployment target | DigitalOcean using Student Developer Pack credit |

## First run

1. Create a new **private** GitHub repository named `ecorevive-os`.
2. Upload these files.
3. Open **Code → Codespaces → Create codespace on main**.
4. In the terminal:

```bash
cp .env.example .env
./scripts/bootstrap.sh
```

5. Open forwarded port `5173`.
6. Sign in using the founder credentials printed by the script.
7. Change the temporary password immediately.

Full instructions: [`docs/setup/FIRST_RUN.md`](docs/setup/FIRST_RUN.md).

## Local run

```bash
cp .env.example .env
docker compose up --build
```

Then:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_ecorevive
docker compose exec backend python manage.py bootstrap_governance \
  --founder-email ujaiwal@outlook.com
```

Frontend: `http://localhost:5173`  
API: `http://localhost:8000/api/`  
API docs: `http://localhost:8000/api/docs/`

## Public impact defaults

The seed values are editable database records rather than hard-coded frontend claims:

- 2,000+ kg e-waste collected for responsible recycling
- 358+ kg paper recycled
- 97+ kg plastic and glass recycled
- 150+ participating households
- 250+ collections

## Honest scope

This is a runnable admissions-grade **Version 0.1 operational MVP and engineering foundation**. It is not yet a city-scale production service. Before public launch, complete pilot testing, security and privacy review, MFA, real geocoding, backups, monitoring, file scanning, and WhatsApp business verification.

See [`docs/roadmap/ROADMAP.md`](docs/roadmap/ROADMAP.md).

## License

AGPL-3.0. See [`LICENSE`](LICENSE).
